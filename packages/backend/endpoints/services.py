"""API REST des services.

CRUD + recherche sur le catalogue de services de la marketplace, plus deux
endpoints qui relaient la *config d'exécution* d'un service (image/code/ressources)
vers le nœud fournisseur via le gateway gRPC. Les données de catalogue vivent dans
la base Postgres locale ; les configs d'exécution vivent sur le nœud fournisseur,
donc ce module ne fait que les transmettre.

Les slugs sont l'identifiant public dans les URLs et sont dérivés du nom du
service ; l'unicité est garantie en ajoutant un court suffixe aléatoire en cas de
collision.
"""

from __future__ import annotations

import math
import uuid

import grpc
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from gateway_stubs import gateway_pb2, gateway_pb2_grpc
from models.service import Service, ServiceStatus
from schemas import PaginatedResponse
from schemas.service import (
    CreateServiceRequest,
    ServicePricingResponse,
    ServiceResponse,
    ServiceSummaryResponse,
    UpdateServiceRequest,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: CreateServiceRequest,
    db: AsyncSession = Depends(get_db),
) -> Service:
    """Publie un nouveau service au catalogue de la marketplace.

    Arguments :
        body: Définition de service validée (nom, tarification, schémas, etc.).
        db: Session de base de données injectée.

    Retourne :
        La ligne Service créée (sérialisée en ServiceResponse, HTTP 201).
    """
    slug = slugify(body.name)

    # Garantit l'unicité du slug en ajoutant un court suffixe si nécessaire
    existing = await db.execute(select(Service).where(Service.slug == slug))
    if existing.scalar_one_or_none() is not None:
        slug = f"{slug}-{str(uuid.uuid7())[:8]}"

    service = Service(
        id=str(uuid.uuid7()),
        provider_site_id=settings.marketplace.site_id,
        name=body.name,
        slug=slug,
        description=body.description,
        category=body.category,
        tags=body.tags,
        service_type=body.service_type.value,
        version=body.version,
        status=body.status.value,
        price_type=body.price_type.value,
        price_amount=body.price_amount,
        currency=body.currency,
        visibility=body.visibility.value,
        execution_mode=body.execution_mode.value,
        input_schema=body.input_schema,
        output_schema=body.output_schema,
        max_concurrency=body.max_concurrency,
        timeout_s=body.timeout_s,
        terms_of_use=body.terms_of_use,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.get("", response_model=PaginatedResponse[ServiceSummaryResponse])
async def list_services(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    service_type: str | None = Query(default=None),
    price_type: str | None = Query(default=None),
    provider_site_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    visibility: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ServiceSummaryResponse]:
    """Liste et recherche les services dans le catalogue de la marketplace.

    Arguments :
        search: Sous-chaîne insensible à la casse comparée au nom et à la description.
        category: Filtre exact de catégorie.
        service_type: Filtre exact de type de service.
        price_type: Filtre exact de modèle de tarification.
        provider_site_id: Restreint aux services d'un seul site fournisseur.
        status: Filtre de statut ; par défaut seulement `active` si omis.
        visibility: Filtre de visibilité ; par défaut seulement `public` si omis.
        page: Numéro de page (base 1).
        per_page: Taille de page (1–100).
        db: Session de base de données injectée.

    Retourne :
        Un PaginatedResponse d'éléments ServiceSummaryResponse plus les métadonnées de pagination.
    """
    query = select(Service)

    # Par défaut : seulement les services actifs + publics, sauf si des filtres priment
    if status is None:
        query = query.where(Service.status == ServiceStatus.active.value)
    else:
        query = query.where(Service.status == status)

    if visibility is None:
        query = query.where(Service.visibility == "public")
    else:
        query = query.where(Service.visibility == visibility)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            Service.name.ilike(pattern) | Service.description.ilike(pattern)
        )
    if category:
        query = query.where(Service.category == category)
    if service_type:
        query = query.where(Service.service_type == service_type)
    if price_type:
        query = query.where(Service.price_type == price_type)
    if provider_site_id:
        query = query.where(Service.provider_site_id == provider_site_id)

    # Compte le total de lignes correspondantes
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Pagine
    offset = (page - 1) * per_page
    result = await db.execute(
        query.order_by(Service.created_at.desc()).offset(offset).limit(per_page)
    )
    services = list(result.scalars().all())

    total_pages = max(1, math.ceil(total / per_page))

    return PaginatedResponse(
        items=[ServiceSummaryResponse.model_validate(s) for s in services],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{slug}/pricing", response_model=ServicePricingResponse)
async def get_service_pricing(slug: str, db: AsyncSession = Depends(get_db)) -> ServicePricingResponse:
    """Renvoie les détails de tarification d'un service public.

    Arguments :
        slug: Slug du service depuis le chemin d'URL.
        db: Session de base de données injectée.

    Retourne :
        Un ServicePricingResponse (type de prix, montant, devise).

    Lève :
        HTTPException: 404 si aucun service public ne correspond au slug.
    """
    result = await db.execute(
        select(Service).where(Service.slug == slug, Service.visibility == "public")
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return ServicePricingResponse.model_validate(service)


@router.get("/{slug}", response_model=ServiceResponse)
async def get_service(
    slug: str,
    include_private: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> Service:
    """Renvoie un service unique par son slug.

    Arguments :
        slug: Slug du service depuis le chemin d'URL.
        include_private: Quand False (défaut), seuls les services publics sont visibles.
        db: Session de base de données injectée.

    Retourne :
        Le Service correspondant (sérialisé en ServiceResponse).

    Lève :
        HTTPException: 404 si aucun service correspondant (et visible) n'est trouvé.
    """
    query = select(Service).where(Service.slug == slug)
    if not include_private:
        query = query.where(Service.visibility == "public")
    result = await db.execute(query)
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.patch("/{slug}", response_model=ServiceResponse)
async def update_service(
    slug: str,
    body: UpdateServiceRequest,
    db: AsyncSession = Depends(get_db),
) -> Service:
    """Met à jour partiellement un service par son slug.

    Seuls les champs présents dans le corps de la requête sont modifiés. Mettre à
    jour le nom régénère le slug (avec un suffixe en cas de collision), et les
    champs enum sont convertis en leurs valeurs chaîne avant écriture.

    Arguments :
        slug: Slug du service à mettre à jour.
        body: Payload de mise à jour partielle ; les champs non définis restent inchangés.
        db: Session de base de données injectée.

    Retourne :
        Le Service mis à jour (sérialisé en ServiceResponse).

    Lève :
        HTTPException: 404 si aucun service ne correspond au slug.
    """
    result = await db.execute(select(Service).where(Service.slug == slug))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    update_data = body.model_dump(exclude_unset=True)

    # Si le nom est mis à jour, régénère le slug
    if "name" in update_data:
        new_slug = slugify(update_data["name"])
        if new_slug != service.slug:
            existing = await db.execute(select(Service).where(Service.slug == new_slug))
            if existing.scalar_one_or_none() is not None:
                new_slug = f"{new_slug}-{str(uuid.uuid7())[:8]}"
            update_data["slug"] = new_slug

    # Applique les conversions d'enum
    for enum_field in ("service_type", "status", "price_type", "visibility", "execution_mode"):
        if enum_field in update_data and hasattr(update_data[enum_field], "value"):
            update_data[enum_field] = update_data[enum_field].value

    for field, value in update_data.items():
        setattr(service, field, value)

    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(slug: str, db: AsyncSession = Depends(get_db)) -> None:
    """Supprime en douceur un service en passant son statut à disabled.

    La ligne est conservée (afin que les invocations existantes se résolvent encore)
    mais masquée du listage actif/public par défaut.

    Arguments :
        slug: Slug du service à désactiver.
        db: Session de base de données injectée.

    Retourne :
        None (HTTP 204).

    Lève :
        HTTPException: 404 si aucun service ne correspond au slug.
    """
    result = await db.execute(select(Service).where(Service.slug == slug))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    service.status = ServiceStatus.disabled.value
    await db.commit()


@router.post("/{slug}/execution-config")
async def register_execution_config(
    slug: str,
    request: Request,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Relaie la config d'exécution d'un service vers le nœud fournisseur via le gateway gRPC.

    La config (image de conteneur ou code inline, commande, args/env par défaut et
    minimums de ressources) est stockée sur le nœud fournisseur, pas dans cette base ;
    cet endpoint valide que le service existe localement, puis transmet la config.
    Seuls les champs présents dans `body` sont posés sur la requête gRPC (les champs
    proto sont optionnels).

    Arguments :
        slug: Slug du service auquel appartient la config.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        body: Dict de config d'exécution brut (image/code/command/args/env/ressources).
        db: Session de base de données injectée.

    Retourne :
        Un dict avec `service_slug` et `created` (True si nouvellement créée).

    Lève :
        HTTPException: 404 si le service est inconnu ; 502 sur erreur gRPC du gateway.
    """
    result = await db.execute(select(Service).where(Service.slug == slug))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    stub = gateway_pb2_grpc.GatewayServiceStub(request.app.state.grpc_channel)

    grpc_request = gateway_pb2.RegisterServiceConfigRequest(
        service_slug=slug,
        retry_count=body.get("retry_count", 0),
    )
    # Ne pose que les champs proto optionnels réellement fournis.
    if body.get("image"):
        grpc_request.image = body["image"]
    if body.get("code"):
        grpc_request.code = body["code"]
    if body.get("command"):
        grpc_request.command = body["command"]
    if body.get("default_args"):
        grpc_request.default_args.update(body["default_args"])
    if body.get("default_env"):
        grpc_request.default_env.update(body["default_env"])
    if body.get("min_cpu") is not None:
        grpc_request.min_cpu = int(body["min_cpu"])
    if body.get("min_gpu") is not None:
        grpc_request.min_gpu = int(body["min_gpu"])
    if body.get("min_mem_mb") is not None:
        grpc_request.min_mem_mb = int(body["min_mem_mb"])

    try:
        resp = await stub.RegisterServiceConfig(grpc_request)
        return {"service_slug": resp.service_slug, "created": resp.created}
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: {e.details() if hasattr(e, 'details') else str(e)}",
        )


@router.get("/{slug}/execution-config")
async def get_execution_config(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Récupère la config d'exécution d'un service depuis le nœud fournisseur via le gateway gRPC.

    Les champs proto optionnels ne sont copiés dans le résultat que s'ils sont posés
    (`HasField`), donc le dict renvoyé contient exactement les champs que le
    fournisseur a configurés.

    Arguments :
        slug: Slug du service dont récupérer la config.
        request: Requête FastAPI, utilisée pour atteindre le canal gRPC partagé.
        db: Session de base de données injectée.

    Retourne :
        Le dict de config d'exécution, ou un dict vide si le fournisseur n'en a pas
        encore enregistré (le gateway renvoie NOT_FOUND).

    Lève :
        HTTPException: 404 si le service est inconnu ; 502 sur autre erreur du gateway.
    """
    result = await db.execute(select(Service).where(Service.slug == slug))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    stub = gateway_pb2_grpc.GatewayServiceStub(request.app.state.grpc_channel)
    try:
        resp = await stub.GetServiceConfig(
            gateway_pb2.GetServiceConfigRequest(service_slug=slug)
        )
        config: dict = {"service_slug": resp.service_slug, "retry_count": resp.retry_count}
        # Ne recopie chaque champ optionnel que si le fournisseur l'a posé.
        if resp.HasField("image"):
            config["image"] = resp.image
        if resp.HasField("code"):
            config["code"] = resp.code
        if resp.HasField("command"):
            config["command"] = resp.command
        if resp.default_args and resp.default_args.fields:
            config["default_args"] = dict(resp.default_args)
        if resp.default_env and resp.default_env.fields:
            config["default_env"] = dict(resp.default_env)
        if resp.HasField("min_cpu"):
            config["min_cpu"] = resp.min_cpu
        if resp.HasField("min_gpu"):
            config["min_gpu"] = resp.min_gpu
        if resp.HasField("min_mem_mb"):
            config["min_mem_mb"] = resp.min_mem_mb
        return config
    except grpc.RpcError as e:
        # Aucune config encore enregistrée est un état normal, pas une erreur.
        if hasattr(e, "code") and e.code() == grpc.StatusCode.NOT_FOUND:
            return {}
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: {e.details() if hasattr(e, 'details') else str(e)}",
        )
