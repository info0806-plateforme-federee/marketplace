"""WebSocket de statut d'invocation.

Pousse le statut d'invocation en direct vers le frontend. L'endpoint fait le pont
entre un appel gRPC en streaming serveur (gateway `StreamJobStatus`) et une
WebSocket : chaque mise à jour de job est mappée vers un `InvocationStatus`,
persistée sur la ligne d'invocation et transmise au client en JSON jusqu'à
atteindre un état terminal.

C'est la contrepartie en mode push de `refresh_invocation_status` (mode poll) dans
`invocations.py`.
"""

from __future__ import annotations

import logging
from datetime import datetime

import grpc
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.database import async_session_factory
from gateway_stubs import gateway_pb2, gateway_pb2_grpc
from models.invocation import Invocation, InvocationStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# Statut de job du nœud -> statut d'invocation de la marketplace.
_JOB_STATUS_MAP = {
    "available": InvocationStatus.accepted.value,
    "assigned": InvocationStatus.accepted.value,
    "pending": InvocationStatus.accepted.value,
    "processing": InvocationStatus.running.value,
    "done": InvocationStatus.succeeded.value,
    "failed": InvocationStatus.failed.value,
}

# Statuts après lesquels aucune mise à jour n'est possible ; le flux se ferme.
_TERMINAL_STATUSES = frozenset({
    InvocationStatus.succeeded.value,
    InvocationStatus.failed.value,
    InvocationStatus.cancelled.value,
})


@router.websocket("/api/invocations/{invocation_id}/ws")
async def invocation_status_stream(websocket: WebSocket, invocation_id: str) -> None:
    """Diffuse en temps réel les mises à jour de statut d'invocation via une WebSocket.

    Ouvre un appel gRPC en streaming serveur vers le `StreamJobStatus` du gateway et
    transmet chaque mise à jour en message JSON au client, en persistant les
    changements sur la ligne d'invocation au fil de l'eau. Court-circuite si
    l'invocation est absente, n'a pas de job, ou est déjà terminale. Ferme le socket
    dès qu'un statut terminal est atteint ; les déconnexions du client et les erreurs
    de flux sont capturées et journalisées.

    Arguments :
        websocket: La connexion WebSocket client acceptée.
        invocation_id: ID de l'invocation à suivre (depuis le chemin d'URL).

    Retourne :
        None. La fonction retourne quand le flux se termine ou que le socket se ferme.
    """
    await websocket.accept()

    # Recherche l'invocation pour obtenir le job_id.
    async with async_session_factory() as session:
        result = await session.execute(
            select(Invocation).where(Invocation.id == invocation_id)
        )
        invocation = result.scalar_one_or_none()

    if invocation is None:
        await websocket.send_json({"error": "Invocation not found"})
        await websocket.close(code=4004)
        return

    if not invocation.job_id:
        await websocket.send_json({"error": "No job associated with this invocation"})
        await websocket.close(code=4004)
        return

    # Si déjà terminale, envoie l'état final et ferme.
    if invocation.status in _TERMINAL_STATUSES:
        await websocket.send_json({
            "invocation_id": invocation.id,
            "status": invocation.status,
            "result_url": invocation.result_url,
            "artifact_url": invocation.artifact_url,
            "error_message": invocation.error_message,
            "started_at": invocation.started_at.isoformat() if invocation.started_at else None,
            "ended_at": invocation.ended_at.isoformat() if invocation.ended_at else None,
            "cost_final": str(invocation.cost_final) if invocation.cost_final is not None else None,
            "terminal": True,
        })
        await websocket.close()
        return

    grpc_channel: grpc.aio.Channel = websocket.app.state.grpc_channel
    stub = gateway_pb2_grpc.GatewayServiceStub(grpc_channel)

    try:
        stream = stub.StreamJobStatus(
            gateway_pb2.StreamJobStatusRequest(
                job_id=invocation.job_id,
                poll_interval_ms=2000,
            )
        )

        async for update in stream:
            new_status = _JOB_STATUS_MAP.get(update.status, invocation.status)

            # Persiste le changement de statut sur l'invocation.
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Invocation).where(Invocation.id == invocation_id)
                )
                inv = result.scalar_one_or_none()
                if inv:
                    changed = False
                    if inv.status != new_status:
                        inv.status = new_status
                        changed = True
                    if update.result_url and inv.result_url != update.result_url:
                        inv.result_url = update.result_url
                        changed = True
                    if update.artifact_url and inv.artifact_url != update.artifact_url:
                        inv.artifact_url = update.artifact_url
                        changed = True
                    if update.error_message:
                        if inv.error_message != update.error_message:
                            inv.error_message = update.error_message
                            changed = True
                    if update.started_at:
                        started_at = datetime.fromisoformat(update.started_at)
                        if inv.started_at != started_at:
                            inv.started_at = started_at
                            changed = True
                    if update.ended_at:
                        ended_at = datetime.fromisoformat(update.ended_at)
                        if inv.ended_at != ended_at:
                            inv.ended_at = ended_at
                            changed = True
                    if (
                        new_status in _TERMINAL_STATUSES
                        and inv.cost_estimated is not None
                        and inv.cost_final != inv.cost_estimated
                    ):
                        inv.cost_final = inv.cost_estimated
                        changed = True
                    if changed:
                        await session.commit()

            is_terminal = new_status in _TERMINAL_STATUSES
            payload = {
                "invocation_id": invocation_id,
                "status": new_status,
                "result_url": update.result_url or None,
                "artifact_url": update.artifact_url or None,
                "error_message": update.error_message or None,
                "started_at": update.started_at or None,
                "ended_at": update.ended_at or None,
                "terminal": is_terminal,
            }
            await websocket.send_json(payload)

            if is_terminal:
                await websocket.close()
                return

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected for invocation %s", invocation_id)
    except grpc.RpcError as e:
        logger.error(
            "gRPC stream error for invocation %s: %s",
            invocation_id,
            e.details() if hasattr(e, "details") else str(e),
        )
        try:
            await websocket.send_json({"error": "Stream error", "detail": str(e)})
            await websocket.close(code=4500)
        except Exception:
            pass
    except Exception:
        logger.exception("Unexpected error in WebSocket for invocation %s", invocation_id)
        try:
            await websocket.close(code=4500)
        except Exception:
            pass
