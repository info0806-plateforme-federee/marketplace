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
    """Register a new federated site in the marketplace."""
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
    """Return all registered federated sites."""
    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str, db: AsyncSession = Depends(get_db)) -> Site:
    """Return a single site by its ID."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site
