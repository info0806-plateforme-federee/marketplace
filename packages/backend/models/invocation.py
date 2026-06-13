"""Modèle ORM Invocation.

Une `Invocation` enregistre une demande d'exécution d'un `Service` : son payload
d'entrée, le `job_id` back-end renvoyé par le gateway/scheduler, le statut
évolutif, les URLs de résultat/artefact et le coût estimé vs final. Elle relie
trois sites — le service, son fournisseur et le consommateur qui a déclenché
l'exécution.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class InvocationStatus(str, enum.Enum):
    """Statut du cycle de vie d'une invocation de service."""

    pending = "pending"
    accepted = "accepted"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class Invocation(Base):
    """Une invocation unique d'un service de la marketplace."""

    __tablename__ = "invocations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    service_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("services.id"), nullable=False
    )
    provider_site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id"), nullable=False
    )
    consumer_site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id"), nullable=False
    )
    # ID du job back-end une fois l'invocation acceptée par le gateway ; null tant
    # qu'elle est en attente. Sert à interroger/streamer le statut depuis le nœud.
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=InvocationStatus.pending.value
    )
    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    result_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    artifact_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_estimated: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    cost_final: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="EUR")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Relations chargées en avance (selectin) pour que les réponses intègrent les
    # lignes liées sans lazy loading. provider_site et consumer_site pointent tous
    # deux vers `sites`, donc `foreign_keys` lève l'ambiguïté sur la colonne suivie.
    service: Mapped[Service] = relationship("Service", lazy="selectin")
    provider_site: Mapped[Site] = relationship(
        "Site", foreign_keys=[provider_site_id], lazy="selectin"
    )
    consumer_site: Mapped[Site] = relationship(
        "Site", foreign_keys=[consumer_site_id], lazy="selectin"
    )
