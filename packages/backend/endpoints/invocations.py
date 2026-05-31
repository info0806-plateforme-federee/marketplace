from __future__ import annotations

import asyncio
import logging
import math
import urllib.error
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

# Mapping from node job statuses to marketplace invocation statuses
_JOB_STATUS_MAP = {
    "available": InvocationStatus.accepted.value,
    "assigned": InvocationStatus.accepted.value,
    "pending": InvocationStatus.accepted.value,
    "processing": InvocationStatus.running.value,
    "done": InvocationStatus.succeeded.value,
    "failed": InvocationStatus.failed.value,
}


def _estimate_cost(service: Service) -> Decimal | None:
    """Compute a cost estimate based on the service pricing model."""
    price_type = service.price_type
    if price_type == PriceType.free.value:
        return Decimal("0")
    if price_type == PriceType.fixed.value:
        return service.price_amount
    # time-based: cost depends on execution duration, unknown upfront
    return None


async def refresh_invocation_status(
    invocation: Invocation,
    grpc_channel: grpc.aio.Channel,
    db: AsyncSession,
) -> None:
    """Poll the gateway for job status and update the invocation."""
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

    # Compute final cost for time-based pricing
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


async def _get_refreshed_invocation(
    invocation_id: str,
    request: Request,
    db: AsyncSession,
) -> Invocation:
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
    """Create a new invocation of a marketplace service."""
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

    # Forward invocation to the gateway → scheduler.
    # Execution config now lives on the provider node; send input_payload as-is.
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
    """List invocations with optional filters."""
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
    """Return a single invocation by ID, auto-refreshing status if pending."""
    return await _get_refreshed_invocation(invocation_id, request, db)


@router.get("/invocations/{invocation_id}/result", response_model=InvocationResultResponse)
async def get_invocation_result(
    invocation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> InvocationResultResponse:
    """Return the result summary for a completed invocation."""
    invocation = await _get_refreshed_invocation(invocation_id, request, db)
    return InvocationResultResponse.model_validate(invocation)


@router.get("/invocations/{invocation_id}/result-file")
async def get_invocation_result_file(
    invocation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Proxy a provider result object through the marketplace API for browsers."""
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
    """Proxy a provider artifact object through the marketplace API for browsers."""
    invocation = await _get_refreshed_invocation(invocation_id, request, db)
    if not invocation.artifact_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not available")

    body, content_type, content_disposition = await _fetch_provider_url(invocation.artifact_url)
    headers = {"content-disposition": content_disposition or "attachment"}
    return Response(content=body, media_type=content_type, headers=headers)
