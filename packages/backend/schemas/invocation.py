from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from models.invocation import InvocationStatus


class InvokeServiceRequest(BaseModel):
    """Payload for invoking a marketplace service."""

    input_payload: dict = {}


class InvocationResponse(BaseModel):
    """Full representation of an invocation returned to clients."""

    id: str
    service_id: str
    job_id: str | None
    provider_site_id: str
    consumer_site_id: str
    status: InvocationStatus
    input_payload: dict
    result_url: str | None
    artifact_url: str | None
    error_message: str | None
    cost_estimated: Decimal | None
    cost_final: Decimal | None
    currency: str
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class InvocationResultResponse(BaseModel):
    """Result summary for a completed invocation."""

    status: InvocationStatus
    result_url: str | None
    artifact_url: str | None
    error_message: str | None
    cost_final: Decimal | None

    class Config:
        from_attributes = True
