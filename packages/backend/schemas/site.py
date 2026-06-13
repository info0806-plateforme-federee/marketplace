"""Schémas Pydantic de requête/réponse pour l'API des sites.

`CreateSiteRequest` valide les données d'enregistrement ; `SiteResponse` sérialise
une ligne ORM `Site` (via `from_attributes = True`) pour les clients.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from models.site import SiteStatus


class CreateSiteRequest(BaseModel):
    """Payload pour enregistrer un nouveau site fédéré."""

    name: str
    description: str | None = None
    grpc_endpoint: str | None = None
    trusted: bool = False


class SiteResponse(BaseModel):
    """Représentation complète d'un site renvoyée aux clients."""

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
