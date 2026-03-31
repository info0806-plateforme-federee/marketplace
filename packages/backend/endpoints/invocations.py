from __future__ import annotations

import logging
import math
import uuid
from decimal import Decimal

import grpc
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
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


def _estimate_cost(service: Service) -> Decimal | None:
    """Compute a cost estimate based on the service pricing model."""
    price_type = service.price_type
    if price_type == PriceType.free.value:
        return Decimal("0")
    if price_type == PriceType.fixed.value:
        return service.price_amount
    # time-based: cost depends on execution duration, unknown upfront
    return None


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

    # Forward invocation to the gateway → scheduler
    # Merge service execution defaults with invoker-provided input_payload.
    # Service defaults act as the base; invoker values override.
    merged_payload: dict = {}
    if service.image:
        merged_payload["image"] = service.image
    if service.code:
        merged_payload["code"] = service.code
    if service.command:
        merged_payload["command"] = service.command
    if service.default_args:
        merged_payload["args"] = dict(service.default_args)
    if service.default_env:
        merged_payload["env"] = dict(service.default_env)
    if service.min_cpu is not None:
        merged_payload["min_cpu"] = service.min_cpu
    if service.min_gpu is not None:
        merged_payload["min_gpu"] = service.min_gpu
    if service.min_mem_mb is not None:
        merged_payload["min_mem_mb"] = service.min_mem_mb
    if service.retry_count:
        merged_payload["retry_count"] = service.retry_count
    # Invoker payload overrides service defaults
    merged_payload.update(body.input_payload)

    stub = gateway_pb2_grpc.GatewayServiceStub(request.app.state.grpc_channel)
    payload_struct = Struct()
    payload_struct.update(merged_payload)

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
async def get_invocation(invocation_id: str, db: AsyncSession = Depends(get_db)) -> Invocation:
    """Return a single invocation by ID."""
    result = await db.execute(select(Invocation).where(Invocation.id == invocation_id))
    invocation = result.scalar_one_or_none()
    if invocation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invocation not found")
    return invocation


@router.get("/invocations/{invocation_id}/result", response_model=InvocationResultResponse)
async def get_invocation_result(
    invocation_id: str, db: AsyncSession = Depends(get_db)
) -> InvocationResultResponse:
    """Return the result summary for a completed invocation."""
    result = await db.execute(select(Invocation).where(Invocation.id == invocation_id))
    invocation = result.scalar_one_or_none()
    if invocation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invocation not found")
    return InvocationResultResponse.model_validate(invocation)
