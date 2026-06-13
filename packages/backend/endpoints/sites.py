"""API REST des sites.

Enregistre et lit les sites fédérés — les pairs (et l'instance locale) qui
fournissent ou consomment des services dans la fédération.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.site import Site
from schemas.site import CreateSiteRequest, SiteResponse

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    body: CreateSiteRequest,
    db: AsyncSession = Depends(get_db),
) -> Site:
    """Enregistre un nouveau site fédéré dans la marketplace.

    Arguments :
        body: Payload d'enregistrement de site (nom, endpoint, drapeau trusted, ...).
        db: Session de base de données injectée.

    Retourne :
        Le Site créé (sérialisé en SiteResponse, HTTP 201).
    """
    site = Site(
        id=str(uuid.uuid7()),
        name=body.name,
        description=body.description,
        grpc_endpoint=body.grpc_endpoint,
        trusted=body.trusted,
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.get("", response_model=list[SiteResponse])
async def list_sites(db: AsyncSession = Depends(get_db)) -> list[Site]:
    """Renvoie tous les sites fédérés enregistrés, les plus récents d'abord.

    Arguments :
        db: Session de base de données injectée.

    Retourne :
        Une liste de lignes Site (sérialisées en SiteResponse).
    """
    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str, db: AsyncSession = Depends(get_db)) -> Site:
    """Renvoie un site unique par son ID.

    Arguments :
        site_id: ID du site depuis le chemin d'URL.
        db: Session de base de données injectée.

    Retourne :
        Le Site correspondant (sérialisé en SiteResponse).

    Lève :
        HTTPException: 404 si aucun site ne correspond à l'ID.
    """
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site
