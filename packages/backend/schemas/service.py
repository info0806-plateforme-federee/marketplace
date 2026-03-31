from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from models.service import ExecutionMode, PriceType, ServiceStatus, ServiceType, Visibility
from schemas.site import SiteResponse


class _SiteSummary(BaseModel):
    """Minimal site info embedded in service responses."""

    id: str
    name: str

    class Config:
        from_attributes = True


class CreateServiceRequest(BaseModel):
    """Payload for publishing a new service to the catalog."""

    name: str
    description: str | None = None
    category: str
    tags: list[str] = []
    service_type: ServiceType
    version: str = "1.0.0"
    status: ServiceStatus = ServiceStatus.draft
    price_type: PriceType
    price_amount: Decimal | None = None
    currency: str = "EUR"
    visibility: Visibility
    execution_mode: ExecutionMode
    input_schema: dict = {}
    output_schema: dict = {}
    max_concurrency: int | None = None
    timeout_s: int | None = None
    image: str | None = None
    code: str | None = None
    command: str | None = None
    default_args: dict = Field(default_factory=dict)
    default_env: dict = Field(default_factory=dict)
    min_cpu: int | None = None
    min_gpu: int | None = None
    min_mem_mb: int | None = None
    retry_count: int = 0
    terms_of_use: str | None = None


class UpdateServiceRequest(BaseModel):
    """Partial update payload — all fields are optional."""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    service_type: ServiceType | None = None
    version: str | None = None
    status: ServiceStatus | None = None
    price_type: PriceType | None = None
    price_amount: Decimal | None = None
    currency: str | None = None
    visibility: Visibility | None = None
    execution_mode: ExecutionMode | None = None
    input_schema: dict | None = None
    output_schema: dict | None = None
    max_concurrency: int | None = None
    timeout_s: int | None = None
    image: str | None = None
    code: str | None = None
    command: str | None = None
    default_args: dict | None = None
    default_env: dict | None = None
    min_cpu: int | None = None
    min_gpu: int | None = None
    min_mem_mb: int | None = None
    retry_count: int | None = None
    terms_of_use: str | None = None


class ServiceResponse(BaseModel):
    """Full representation of a service returned to clients."""

    id: str
    provider_site_id: str
    name: str
    slug: str
    description: str | None
    category: str
    tags: list
    service_type: str
    version: str
    status: str
    price_type: str
    price_amount: Decimal | None
    currency: str
    visibility: str
    execution_mode: str
    input_schema: dict
    output_schema: dict
    max_concurrency: int | None
    timeout_s: int | None
    image: str | None = None
    code: str | None = None
    command: str | None = None
    default_args: dict = Field(default_factory=dict)
    default_env: dict = Field(default_factory=dict)
    min_cpu: int | None = None
    min_gpu: int | None = None
    min_mem_mb: int | None = None
    retry_count: int = 0
    terms_of_use: str | None
    created_at: datetime
    updated_at: datetime
    provider_site: SiteResponse | None = None

    class Config:
        from_attributes = True


class ServiceSummaryResponse(BaseModel):
    """Condensed service representation used in list endpoints."""

    id: str
    name: str
    slug: str
    description: str | None
    category: str
    tags: list
    service_type: str
    price_type: str
    price_amount: Decimal | None
    currency: str
    status: str
    provider_site: _SiteSummary | None = None

    class Config:
        from_attributes = True


class ServicePricingResponse(BaseModel):
    """Pricing details for a service."""

    price_type: str
    price_amount: Decimal | None
    currency: str

    class Config:
        from_attributes = True
