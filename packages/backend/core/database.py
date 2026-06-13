"""Moteur de base de données, fabrique de sessions et base ORM.

Met en place l'unique moteur SQLAlchemy asynchrone et une fabrique de sessions
utilisés dans tout le backend. `Base` est la base déclarative dont hérite chaque
modèle ORM ; `get_db` est la dépendance FastAPI qui fournit une session aux
handlers de requête.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# Un moteur par processus ; l'URL asynchrone (asyncpg) provient des réglages.
engine = create_async_engine(settings.database.async_url)
# expire_on_commit=False garde les attributs utilisables après commit (p. ex. pour
# construire une réponse depuis un objet qu'on vient de committer) sans nouvelle requête.
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base déclarative partagée par tous les modèles ORM (collecte les métadonnées de tables)."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dépendance FastAPI fournissant une session de base de données par requête.

    Le bloc `async with` garantit la fermeture de la session à la fin de la requête.

    Génère :
        Une `AsyncSession` liée au moteur partagé.
    """
    async with async_session_factory() as session:
        yield session
