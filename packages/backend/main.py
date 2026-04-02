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
from models.invocation import Invocation, InvocationStatus
from models.site import Site

setup_logging()
logger = logging.getLogger(__name__)


async def _seed_local_site() -> None:
    """Ensure the local site record exists in the database."""
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
    """Background task that periodically refreshes accepted/running invocations."""
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
    await _seed_local_site()
    app.state.grpc_channel = grpc.aio.insecure_channel(settings.gateway.url)
    logger.info("Gateway gRPC channel: %s", settings.gateway.url)
    poller_task = asyncio.create_task(_poll_pending_invocations(app.state.grpc_channel))
    yield
    poller_task.cancel()
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
    """Liveness probe endpoint."""
    return {"status": "ok"}
