"""Schémas Pydantic de requête/réponse pour l'API des invocations.

`InvokeServiceRequest` est le payload d'entrée soumis par un consommateur ; les
schémas de réponse (`InvocationResponse`, `InvocationResultResponse`) sont
construits depuis les lignes ORM `Invocation` via `from_attributes = True`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from models.invocation import InvocationStatus


class InvokeServiceRequest(BaseModel):
    """Payload pour invoquer un service de la marketplace."""

    input_payload: dict = {}


class InvocationResponse(BaseModel):
    """Représentation complète d'une invocation renvoyée aux clients."""

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
    """Résumé de résultat pour une invocation terminée."""

    status: InvocationStatus
    result_url: str | None
    artifact_url: str | None
    error_message: str | None
    cost_final: Decimal | None

    class Config:
        from_attributes = True
