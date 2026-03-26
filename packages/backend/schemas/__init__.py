from typing import Generic, TypeVar

from pydantic import BaseModel

from schemas.invocation import InvocationResponse, InvocationResultResponse, InvokeServiceRequest
from schemas.service import (
    CreateServiceRequest,
    ServicePricingResponse,
    ServiceResponse,
    ServiceSummaryResponse,
    UpdateServiceRequest,
)
from schemas.site import CreateSiteRequest, SiteResponse

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated wrapper for list endpoints."""

    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


__all__ = [
    "CreateServiceRequest",
    "CreateSiteRequest",
    "InvocationResponse",
    "InvocationResultResponse",
    "InvokeServiceRequest",
    "PaginatedResponse",
    "ServicePricingResponse",
    "ServiceResponse",
    "ServiceSummaryResponse",
    "SiteResponse",
    "UpdateServiceRequest",
]
