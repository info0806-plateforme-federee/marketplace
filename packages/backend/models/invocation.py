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
    """Lifecycle status of a service invocation."""

    pending = "pending"
    accepted = "accepted"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class Invocation(Base):
    """A single invocation of a marketplace service."""

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

    service: Mapped[Service] = relationship("Service", lazy="selectin")
    provider_site: Mapped[Site] = relationship(
        "Site", foreign_keys=[provider_site_id], lazy="selectin"
    )
    consumer_site: Mapped[Site] = relationship(
        "Site", foreign_keys=[consumer_site_id], lazy="selectin"
    )
