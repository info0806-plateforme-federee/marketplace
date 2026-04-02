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

_JOB_STATUS_MAP = {
    "available": InvocationStatus.accepted.value,
    "assigned": InvocationStatus.accepted.value,
    "pending": InvocationStatus.accepted.value,
    "processing": InvocationStatus.running.value,
    "done": InvocationStatus.succeeded.value,
    "failed": InvocationStatus.failed.value,
}

_TERMINAL_STATUSES = frozenset({
    InvocationStatus.succeeded.value,
    InvocationStatus.failed.value,
    InvocationStatus.cancelled.value,
})


@router.websocket("/api/invocations/{invocation_id}/ws")
async def invocation_status_stream(websocket: WebSocket, invocation_id: str) -> None:
    """Stream real-time invocation status updates via WebSocket.

    Opens a gRPC server-streaming call to the gateway's StreamJobStatus
    and forwards each update as a JSON message to the WebSocket client.
    """
    await websocket.accept()

    # Look up the invocation to get the job_id.
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

    # If already terminal, send final state and close.
    if invocation.status in _TERMINAL_STATUSES:
        await websocket.send_json({
            "invocation_id": invocation.id,
            "status": invocation.status,
            "result_payload": invocation.result_payload,
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

            # Persist status change to the invocation.
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Invocation).where(Invocation.id == invocation_id)
                )
                inv = result.scalar_one_or_none()
                if inv and inv.status != new_status:
                    inv.status = new_status
                    if update.result_payload and update.result_payload.fields:
                        inv.result_payload = dict(update.result_payload)
                    if update.error_message:
                        inv.error_message = update.error_message
                    if update.started_at:
                        inv.started_at = datetime.fromisoformat(update.started_at)
                    if update.ended_at:
                        inv.ended_at = datetime.fromisoformat(update.ended_at)
                    if new_status in _TERMINAL_STATUSES and inv.cost_estimated is not None:
                        inv.cost_final = inv.cost_estimated
                    await session.commit()

            is_terminal = new_status in _TERMINAL_STATUSES
            payload = {
                "invocation_id": invocation_id,
                "status": new_status,
                "result_payload": dict(update.result_payload) if update.result_payload and update.result_payload.fields else None,
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
