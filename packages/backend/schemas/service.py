"""Schémas Pydantic de requête/réponse pour l'API des services.

Ils définissent les formes JSON que la couche HTTP accepte et renvoie, distinctes
des modèles ORM SQLAlchemy. Les schémas de requête valident les payloads entrants
(et réutilisent les enums du modèle pour les champs contraints) ; les schémas de
réponse posent `from_attributes = True` afin d'être construits directement depuis
les objets ORM.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from models.service import ExecutionMode, PriceType, ServiceStatus, ServiceType, Visibility
from schemas.site import SiteResponse


class _SiteSummary(BaseModel):
    """Infos minimales de site intégrées dans les réponses de service."""

    id: str
    name: str

    class Config:
        from_attributes = True


class CreateServiceRequest(BaseModel):
    """Payload pour publier un nouveau service au catalogue."""

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
    terms_of_use: str | None = None


class UpdateServiceRequest(BaseModel):
    """Payload de mise à jour partielle — tous les champs sont optionnels."""

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
    terms_of_use: str | None = None


class ServiceResponse(BaseModel):
    """Représentation complète d'un service renvoyée aux clients."""

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
    terms_of_use: str | None
    created_at: datetime
    updated_at: datetime
    provider_site: SiteResponse | None = None

    class Config:
        from_attributes = True


class ServiceSummaryResponse(BaseModel):
    """Représentation condensée d'un service utilisée dans les endpoints de liste."""

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
    """Détails de tarification d'un service."""

    price_type: str
    price_amount: Decimal | None
    currency: str

    class Config:
        from_attributes = True
