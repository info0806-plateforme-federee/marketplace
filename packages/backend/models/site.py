"""Modèle ORM Site.

Un `Site` est un nœud de la fédération : soit l'instance locale de la marketplace,
soit un pair distant qui fournit/consomme des services. `grpc_endpoint` indique où
joindre son gateway, et `trusted` marque les sites dont les services peuvent être
invoqués sans vérification supplémentaire.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SiteStatus(str, enum.Enum):
    """Valeurs de statut d'un site fédéré."""

    active = "active"
    inactive = "inactive"
    pending = "pending"


class Site(Base):
    """Un site fédéré enregistré dans la marketplace."""

    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    grpc_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=SiteStatus.active.value)
    trusted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
