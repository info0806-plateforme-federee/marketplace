from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from models.site import SiteStatus


class CreateSiteRequest(BaseModel):
    """Payload for registering a new federated site."""

    name: str
    description: str | None = None
    grpc_endpoint: str | None = None
    trusted: bool = False


class SiteResponse(BaseModel):
    """Full representation of a site returned to clients."""

    id: str
    name: str
    description: str | None
    grpc_endpoint: str | None
    status: SiteStatus
    trusted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
