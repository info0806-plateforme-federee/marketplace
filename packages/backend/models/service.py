from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB  # retained for tags / input_schema / output_schema
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ServiceStatus(str, enum.Enum):
    """Publication status of a service."""

    active = "active"
    disabled = "disabled"
    draft = "draft"
    deprecated = "deprecated"


class ServiceType(str, enum.Enum):
    """Category of computation a service provides."""

    compute = "compute"
    data = "data"
    model = "model"
    utility = "utility"


class PriceType(str, enum.Enum):
    """Billing model for a service."""

    free = "free"
    fixed = "fixed"
    time = "time"


class Visibility(str, enum.Enum):
    """Access level for a service."""

    public = "public"
    private = "private"
    restricted = "restricted"


class ExecutionMode(str, enum.Enum):
    """Whether the service runs synchronously or asynchronously."""

    sync = "sync"
    async_ = "async"


class Service(Base):
    """A service listed in the federated marketplace catalog."""

    __tablename__ = "services"
    __table_args__ = (UniqueConstraint("slug", name="uq_services_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    provider_site_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sites.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, server_default="1.0.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=ServiceStatus.draft.value)
    price_type: Mapped[str] = mapped_column(String(50), nullable=False)
    price_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="EUR")
    visibility: Mapped[str] = mapped_column(String(50), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    max_concurrency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    terms_of_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    provider_site: Mapped[Site] = relationship("Site", lazy="selectin")
