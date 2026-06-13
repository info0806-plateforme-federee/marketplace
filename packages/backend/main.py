"""Point d'entrée de l'application API de la marketplace.

Construit l'app FastAPI et câble son cycle de vie (`lifespan`) :
  - seede l'enregistrement du site local et les services de démonstration intégrés,
  - ouvre le canal gRPC partagé vers le gateway du nœud (stocké sur
    `app.state.grpc_channel`),
  - lance deux tâches d'arrière-plan : l'enregistrement des configs d'exécution de
    démo sur le nœud fournisseur, et la réconciliation périodique des statuts
    d'invocation en cours,
  - démonte tout cela à l'arrêt.

Tous les routeurs sont montés sous `/api` (sauf le routeur WebSocket), et une
sonde de vivacité `/healthz` est exposée.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import grpc
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from core.config import settings
from core.database import async_session_factory, engine
from core.logging import setup_logging
from endpoints.invocations import refresh_invocation_status, router as invocations_router
from endpoints.services import router as services_router
from endpoints.sites import router as sites_router
from endpoints.ws import router as ws_router
from fixtures.demo_services import register_demo_execution_configs, seed_demo_services
from models.invocation import Invocation, InvocationStatus
from models.site import Site

setup_logging()
logger = logging.getLogger(__name__)


async def _seed_local_site() -> None:
    """Garantit l'existence de l'enregistrement du site local dans la base.

    Crée une ligne Site de confiance pour le `site_id` configuré de cette instance
    s'il n'en existe pas déjà une ; idempotent entre redémarrages.

    Retourne :
        None.
    """
    async with async_session_factory() as session:
        result = await session.execute(
            select(Site).where(Site.id == settings.marketplace.site_id)
        )
        if result.scalar_one_or_none() is None:
            site = Site(
                id=settings.marketplace.site_id,
                name=settings.marketplace.site_name,
                description="Local site (auto-created)",
                trusted=True,
            )
            session.add(site)
            await session.commit()
            logger.info("Seeded local site: %s", settings.marketplace.site_id)


async def _poll_pending_invocations(grpc_channel: grpc.aio.Channel) -> None:
    """Réconcilie périodiquement les invocations en cours face au gateway.

    Toutes les 30 s, charge toutes les invocations acceptées/en cours et rafraîchit
    chacune. C'est un filet de sécurité pour que les statuts convergent même si un
    client n'ouvre jamais le flux WebSocket. Tourne jusqu'à annulation à l'arrêt ;
    les erreurs par cycle sont journalisées et la boucle continue.

    Arguments :
        grpc_channel: Canal ouvert vers le gateway, partagé avec le chemin de requête.

    Retourne :
        None. Ne retourne jamais normalement ; tourne jusqu'à l'annulation de la tâche.
    """
    while True:
        await asyncio.sleep(30)
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Invocation).where(
                        Invocation.status.in_([
                            InvocationStatus.accepted.value,
                            InvocationStatus.running.value,
                        ])
                    )
                )
                invocations = result.scalars().all()
                for inv in invocations:
                    await refresh_invocation_status(inv, grpc_channel, session)
        except Exception:
            logger.exception("Error in invocation polling loop")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le démarrage/l'arrêt : seed des données, ouverture du canal gRPC, tâches d'arrière-plan.

    Tout ce qui précède `yield` s'exécute au démarrage ; tout ce qui suit s'exécute
    à l'arrêt (annulation des tâches d'arrière-plan, fermeture du canal gRPC,
    libération du moteur).

    Arguments :
        app: L'application FastAPI dont l'attribut `state` détient le canal gRPC partagé.

    Génère :
        Le contrôle à l'application en cours d'exécution pour toute sa durée de vie.
    """
    await _seed_local_site()
    app.state.grpc_channel = grpc.aio.insecure_channel(settings.gateway.url)
    logger.info("Gateway gRPC channel: %s", settings.gateway.url)
    async with async_session_factory() as session:
        await seed_demo_services(session)
    fixtures_task = asyncio.create_task(
        register_demo_execution_configs(app.state.grpc_channel)
    )
    poller_task = asyncio.create_task(_poll_pending_invocations(app.state.grpc_channel))
    yield
    poller_task.cancel()
    fixtures_task.cancel()
    await app.state.grpc_channel.close()
    await engine.dispose()


app = FastAPI(title="Marketplace API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(sites_router)
api_router.include_router(services_router)
api_router.include_router(invocations_router)
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    """Endpoint de sonde de vivacité.

    Retourne :
        Un payload constant `{"status": "ok"}` lorsque le processus répond.
    """
    return {"status": "ok"}
