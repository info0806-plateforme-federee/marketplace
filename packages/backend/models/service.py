"""Modèle ORM Service.

Un `Service` est une entrée de catalogue annoncée dans la marketplace : ce qu'il
fait, qui le fournit, comment il est tarifé, et les schémas JSON d'entrée/sortie
qu'un consommateur doit respecter lors de l'invocation. Les enums ci-dessous
contraignent les colonnes stockées en simples chaînes (gardées en chaînes plutôt
qu'en enums SQL pour que les valeurs puissent évoluer sans migration).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB  # conservé pour tags / input_schema / output_schema
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ServiceStatus(str, enum.Enum):
    """Statut de publication d'un service."""

    active = "active"
    disabled = "disabled"
    draft = "draft"
    deprecated = "deprecated"


class ServiceType(str, enum.Enum):
    """Catégorie de calcul fournie par un service."""

    compute = "compute"
    data = "data"
    model = "model"
    utility = "utility"


class PriceType(str, enum.Enum):
    """Modèle de facturation d'un service."""

    free = "free"
    fixed = "fixed"
    time = "time"


class Visibility(str, enum.Enum):
    """Niveau d'accès d'un service."""

    public = "public"
    private = "private"
    restricted = "restricted"


class ExecutionMode(str, enum.Enum):
    """Indique si le service s'exécute de façon synchrone ou asynchrone."""

    sync = "sync"
    async_ = "async"


class Service(Base):
    """Un service listé dans le catalogue de la marketplace fédérée."""

    __tablename__ = "services"
    # `slug` est l'identifiant lisible et compatible URL utilisé dans les chemins d'API.
    __table_args__ = (UniqueConstraint("slug", name="uq_services_slug"),)

    # uuid7 est ordonné dans le temps, donc les clés primaires se trient aussi
    # approximativement par date de création.
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    # Site qui possède/héberge ce service (le fournisseur dans la fédération).
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
    # Schémas JSON décrivant l'entrée d'invocation attendue et la sortie produite.
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

    # Charge le Site fournisseur en avance via un SELECT séparé pour que les réponses
    # puissent intégrer les détails du site sans aller-retour de lazy-load dans la session async.
    provider_site: Mapped[Site] = relationship("Site", lazy="selectin")
