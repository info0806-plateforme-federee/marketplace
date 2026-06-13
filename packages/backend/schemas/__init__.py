"""Exports du paquet de schémas et enveloppe de pagination partagée.

Réexporte les schémas de requête/réponse par ressource et définit
`PaginatedResponse`, l'enveloppe générique que renvoie chaque endpoint de liste.
"""

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
    """Enveloppe paginée générique pour les endpoints de liste.

    Le paramètre de type `T` est le schéma d'élément (p. ex. `ServiceSummaryResponse`).
    `total` est le nombre total de lignes correspondantes ; `total_pages` est dérivé
    de `total` et `per_page`.
    """

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
