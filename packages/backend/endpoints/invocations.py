"""API REST des invocations.

Pilote le cycle de vie d'une invocation de service :
  1. `invoke_service` enregistre une Invocation, la relaie au gateway
     (gRPC InvokeService) et stocke le `job_id` renvoyé.
  2. Le nœud exécute le job de façon asynchrone ; le statut est réconcilié soit par
     le poller d'arrière-plan (voir main.py), soit par le flux WebSocket (voir
     ws.py), soit paresseusement à la lecture via `refresh_invocation_status`.
  3. Les fichiers de résultat/artefact produits par le fournisseur sont relayés au
     navigateur via cette API, de sorte que le frontend ne dialogue jamais
     directement avec le stockage du fournisseur.

Les statuts de job du nœud sont mappés sur les valeurs `InvocationStatus` de la
marketplace via `_JOB_STATUS_MAP`.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from decimal import Decimal

import grpc
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from google.protobuf.struct_pb2 import Struct
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from gateway_stubs import gateway_pb2, gateway_pb2_grpc
from models.invocation import Invocation, InvocationStatus
from models.service import PriceType, Service
from schemas import PaginatedResponse
from schemas.invocation import InvocationResponse, InvocationResultResponse, InvokeServiceRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["invocations"])

# Mapping des statuts de job du nœud vers les statuts d'invocation de la marketplace
_JOB_STATUS_MAP = {
    "available": InvocationStatus.accepted.value,
    "assigned": InvocationStatus.accepted.value,
    "pending": InvocationStatus.accepted.value,
    "processing": InvocationStatus.running.value,
    "done": InvocationStatus.succeeded.value,
    "failed": InvocationStatus.failed.value,
}


def _estimate_cost(service: Service) -> Decimal | None:
    """Calcule une estimation de coût a priori à partir du modèle de tarification du service.

    Arguments :
        service: Le service en cours d'invocation.

    Retourne :
        `Decimal("0")` pour les services gratuits, le prix fixe pour une tarification
        fixe, ou None pour une tarification au temps (coût inconnu tant que le job
        n'est pas terminé).
    """
    price_type = service.price_type
    if price_type == PriceType.free.value:
        return Decimal("0")
    if price_type == PriceType.fixed.value:
        return service.price_amount
    # au temps : le coût dépend de la durée d'exécution, inconnu a priori
    return None


async def refresh_invocation_status(
    invocation: Invocation,
    grpc_channel: grpc.aio.Channel,
    db: AsyncSession,
) -> None:
    """Interroge le gateway une fois pour le statut du job et réconcilie la ligne d'invocation.

    Lit le dernier statut/les URLs/horodatages du job depuis le gateway et réécrit
    tout changement, en committant uniquement si quelque chose a réellement changé.
    Pour les jobs au temps réussis, finalise `cost_final` depuis l'estimation.
    Ne fait rien si l'invocation n'a pas encore de `job_id`, et les erreurs du
    gateway sont journalisées et avalées.

    Arguments :
        invocation: L'invocation à rafraîchir (mutée sur place en cas de changement).
        grpc_channel: Canal ouvert vers le gateway.
        db: Session utilisée pour committer les éventuels changements.

    Retourne :
        None.
    """
    if not invocation.job_id:
        return

    stub = gateway_pb2_grpc.GatewayServiceStub(grpc_channel)
    try:
        resp = await stub.GetJobStatus(
            gateway_pb2.GetJobStatusRequest(job_id=invocation.job_id)
        )
    except grpc.RpcError as e:
        logger.warning(
            "Failed to poll status for invocation %s (job %s): %s",
            invocation.id, invocation.job_id, e,
        )
        return

    previous_status = invocation.status
    new_status = _JOB_STATUS_MAP.get(resp.status, previous_status)
    changed = False

    if new_status != previous_status:
        invocation.status = new_status
        changed = True

    if resp.result_url and invocation.result_url != resp.result_url:
        invocation.result_url = resp.result_url
        changed = True

    if resp.artifact_url and invocation.artifact_url != resp.artifact_url:
        invocation.artifact_url = resp.artifact_url
        changed = True

    if resp.error_message and invocation.error_message != resp.error_message:
        invocation.error_message = resp.error_message
        changed = True

    if resp.started_at:
        started_at = datetime.fromisoformat(resp.started_at)
        if invocation.started_at != started_at:
            invocation.started_at = started_at
            changed = True

    if resp.ended_at:
        ended_at = datetime.fromisoformat(resp.ended_at)
        if invocation.ended_at != ended_at:
            invocation.ended_at = ended_at
            changed = True

    if not changed:
        return

    # Calcule le coût final pour la tarification au temps
    if (
        new_status == InvocationStatus.succeeded.value
        and invocation.cost_estimated is not None
        and invocation.cost_final != invocation.cost_estimated
    ):
        invocation.cost_final = invocation.cost_estimated
        changed = True

    if not changed:
        return

    await db.commit()
    logger.info(
        "Invocation %s updated: %s → %s",
        invocation.id, previous_status, invocation.status,
    )


async def _fetch_provider_url(url: str) -> tuple[bytes, str, str | None]:
    """Télécharge un objet du fournisseur (résultat/artefact) en HTTP, hors de la boucle d'événements.

    L'appel bloquant `urllib` est exécuté dans un thread pour ne pas bloquer le
    serveur asynchrone. Les erreurs HTTP et réseau sont traduites en HTTPException.

    Arguments :
        url: URL complète de l'objet du fournisseur à récupérer (GET).

    Retourne :
        Un tuple `(body, content_type, content_disposition)` ; la disposition est
        None quand le fournisseur n'en a pas envoyé.

    Lève :
        HTTPException: le statut amont sur erreur HTTP, ou 502 sur échec
            réseau/timeout.
    """
    def _fetch() -> tuple[bytes, str, str | None]:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("content-type") or "application/octet-stream"
            content_disposition = resp.headers.get("content-disposition")
            return resp.read(), content_type, content_disposition

    try:
        return await asyncio.to_thread(_fetch)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(
            status_code=exc.code,
            detail=detail or "Provider object fetch failed",
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider object fetch failed: {exc}",
        ) from exc


def _content_disposition_with_filename(
    content_disposition: str | None,
    url: str,
    fallback_filename: str,
) -> str:
    """Construit un en-tête Content-Disposition qui porte toujours un nom de fichier.

    Si le fournisseur a déjà fourni un `filename`, son en-tête est transmis tel
    quel. Sinon, un nom de fichier est dérivé du chemin de l'URL (en repli sur
    `fallback_filename`) et assaini pour être sûr dans l'en-tête.

    Arguments :
        content_disposition: Le Content-Disposition du fournisseur, le cas échéant.
        url: URL source, utilisée pour dériver un nom de fichier s'il en manque un.
        fallback_filename: Nom à utiliser quand l'URL ne donne rien d'exploitable.

    Retourne :
        Une valeur d'en-tête Content-Disposition contenant un nom de fichier entre guillemets.
    """
    if content_disposition and re.search(r"\bfilename\*?=", content_disposition, re.I):
        return content_disposition

    parsed = urllib.parse.urlparse(url)
    filename = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
    if not filename or filename in {".", ".."}:
        filename = fallback_filename

    safe_filename = filename.replace("\\", "_").replace('"', "")
    disposition_type = (content_disposition or "attachment").split(";", 1)[0].strip()
    if not disposition_type:
        disposition_type = "attachment"
    return f'{disposition_type}; filename="{safe_filename}"'


async def _get_refreshed_invocation(
    invocation_id: str,
    request: Request,
    db: AsyncSession,
) -> Invocation:
    """Charge une invocation, en rafraîchissant son statut depuis le gateway si en cours.

    Partagée par les endpoints de lecture : si l'invocation est encore
    acceptée/en cours, elle est réconciliée face au gateway avant d'être renvoyée
    afin que les appelants voient l'état le plus frais.

    Arguments :
        invocation_id: ID de l'invocation à charger.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        db: Session de base de données injectée.

    Retourne :
        L'Invocation (éventuellement tout juste rafraîchie).

    Lève :
        HTTPException: 404 si aucune invocation ne correspond à l'ID.
    """
    result = await db.execute(select(Invocation).where(Invocation.id == invocation_id))
    invocation = result.scalar_one_or_none()
    if invocation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invocation not found")

    if invocation.status in (InvocationStatus.accepted.value, InvocationStatus.running.value):
        await refresh_invocation_status(invocation, request.app.state.grpc_channel, db)
        await db.refresh(invocation)

    return invocation


@router.post("/services/{slug}/invoke", response_model=InvocationResponse, status_code=status.HTTP_201_CREATED)
async def invoke_service(
    slug: str,
    request: Request,
    body: InvokeServiceRequest,
    db: AsyncSession = Depends(get_db),
) -> Invocation:
    """Crée une nouvelle invocation d'un service de la marketplace et la dépêche.

    Persiste une invocation `pending`, puis la relaie au gateway. En cas de succès,
    l'invocation est marquée `accepted` avec le `job_id` renvoyé ; en cas d'erreur
    du gateway, elle est marquée `failed` avec le message d'erreur. Dans tous les
    cas, la ligne d'invocation est renvoyée (les échecs sont enregistrés, pas levés).

    Arguments :
        slug: Slug du service à invoquer.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        body: Payload d'entrée de l'invocation.
        db: Session de base de données injectée.

    Retourne :
        L'Invocation créée (HTTP 201), dans l'état `accepted` ou `failed`.

    Lève :
        HTTPException: 404 si le service est inconnu ; 403 s'il n'est pas public.
    """
    result = await db.execute(select(Service).where(Service.slug == slug))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if service.visibility != "public":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service is not publicly accessible")

    invocation = Invocation(
        id=str(uuid.uuid7()),
        service_id=service.id,
        provider_site_id=service.provider_site_id,
        consumer_site_id=settings.marketplace.site_id,
        status=InvocationStatus.pending.value,
        input_payload=body.input_payload,
        cost_estimated=_estimate_cost(service),
        currency=service.currency,
    )
    db.add(invocation)
    await db.commit()
    await db.refresh(invocation)

    # Relaie l'invocation au gateway → scheduler.
    # La config d'exécution vit désormais sur le nœud fournisseur ; envoie input_payload tel quel.
    stub = gateway_pb2_grpc.GatewayServiceStub(request.app.state.grpc_channel)
    payload_struct = Struct()
    payload_struct.update(body.input_payload)

    grpc_request = gateway_pb2.InvokeServiceRequest(
        invocation_id=invocation.id,
        service_name=service.name,
        service_slug=service.slug,
        service_type=service.service_type,
        tags=service.tags or [],
        execution_mode=service.execution_mode,
        input_payload=payload_struct,
    )
    if service.timeout_s is not None:
        grpc_request.timeout_s = service.timeout_s

    try:
        grpc_response = await stub.InvokeService(grpc_request)
        invocation.job_id = grpc_response.job_id
        invocation.status = InvocationStatus.accepted.value
        await db.commit()
        await db.refresh(invocation)
        logger.info(
            "Invocation %s accepted, job_id=%s",
            invocation.id,
            grpc_response.job_id,
        )
    except grpc.RpcError as e:
        invocation.status = InvocationStatus.failed.value
        invocation.error_message = f"Gateway error: {e.details() if hasattr(e, 'details') else str(e)}"
        await db.commit()
        await db.refresh(invocation)
        logger.error(
            "Invocation %s failed: %s",
            invocation.id,
            invocation.error_message,
        )

    return invocation


@router.get("/invocations", response_model=PaginatedResponse[InvocationResponse])
async def list_invocations(
    status: str | None = Query(default=None),
    service_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[InvocationResponse]:
    """Liste les invocations avec des filtres optionnels, les plus récentes d'abord.

    Arguments :
        status: Filtre de statut exact optionnel.
        service_id: Filtre optionnel sur les invocations d'un seul service.
        page: Numéro de page (base 1).
        per_page: Taille de page (1–100).
        db: Session de base de données injectée.

    Retourne :
        Un PaginatedResponse d'éléments InvocationResponse plus les métadonnées de pagination.
    """
    query = select(Invocation)

    if status:
        query = query.where(Invocation.status == status)
    if service_id:
        query = query.where(Invocation.service_id == service_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(Invocation.created_at.desc()).offset(offset).limit(per_page)
    )
    invocations = list(result.scalars().all())

    total_pages = max(1, math.ceil(total / per_page))

    return PaginatedResponse(
        items=[InvocationResponse.model_validate(i) for i in invocations],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/invocations/{invocation_id}", response_model=InvocationResponse)
async def get_invocation(
    invocation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Invocation:
    """Renvoie une invocation unique par ID, en rafraîchissant le statut si encore en cours.

    Arguments :
        invocation_id: ID depuis le chemin d'URL.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        db: Session de base de données injectée.

    Retourne :
        L'Invocation (sérialisée en InvocationResponse).

    Lève :
        HTTPException: 404 si aucune invocation ne correspond à l'ID.
    """
    return await _get_refreshed_invocation(invocation_id, request, db)


@router.get("/invocations/{invocation_id}/result", response_model=InvocationResultResponse)
async def get_invocation_result(
    invocation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> InvocationResultResponse:
    """Renvoie le résumé de résultat (statut, URLs, coût final) d'une invocation.

    Arguments :
        invocation_id: ID depuis le chemin d'URL.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        db: Session de base de données injectée.

    Retourne :
        Un InvocationResultResponse construit depuis l'invocation (rafraîchie).

    Lève :
        HTTPException: 404 si aucune invocation ne correspond à l'ID.
    """
    invocation = await _get_refreshed_invocation(invocation_id, request, db)
    return InvocationResultResponse.model_validate(invocation)


@router.get("/invocations/{invocation_id}/result-file")
async def get_invocation_result_file(
    invocation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Relaie l'objet de résultat du fournisseur via l'API de la marketplace.

    Le relais évite au navigateur d'avoir besoin d'un accès direct au stockage du
    fournisseur et préserve le type de contenu/la disposition amont.

    Arguments :
        invocation_id: ID depuis le chemin d'URL.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        db: Session de base de données injectée.

    Retourne :
        Une Response portant les octets bruts du résultat avec le type de contenu amont.

    Lève :
        HTTPException: 404 si l'invocation ou son URL de résultat est absente ; 502
            sur échec de récupération chez le fournisseur.
    """
    invocation = await _get_refreshed_invocation(invocation_id, request, db)
    if not invocation.result_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not available")

    body, content_type, content_disposition = await _fetch_provider_url(invocation.result_url)
    headers = {}
    if content_disposition:
        headers["content-disposition"] = content_disposition
    return Response(content=body, media_type=content_type, headers=headers)


@router.get("/invocations/{invocation_id}/artifact")
async def get_invocation_artifact(
    invocation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Relaie le fichier artefact du fournisseur via l'API de la marketplace.

    Comme l'endpoint de résultat, mais pose toujours un Content-Disposition avec un
    nom de fichier de téléchargement raisonnable (en repli sur `<service-slug>-artifact`).

    Arguments :
        invocation_id: ID depuis le chemin d'URL.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        db: Session de base de données injectée.

    Retourne :
        Une Response portant les octets de l'artefact avec un en-tête de nom de fichier.

    Lève :
        HTTPException: 404 si l'invocation ou son URL d'artefact est absente ; 502
            sur échec de récupération chez le fournisseur.
    """
    invocation = await _get_refreshed_invocation(invocation_id, request, db)
    if not invocation.artifact_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not available")

    body, content_type, content_disposition = await _fetch_provider_url(invocation.artifact_url)
    headers = {
        "content-disposition": _content_disposition_with_filename(
            content_disposition,
            invocation.artifact_url,
            f"{invocation.service.slug}-artifact",
        )
    }
    return Response(content=body, media_type=content_type, headers=headers)
