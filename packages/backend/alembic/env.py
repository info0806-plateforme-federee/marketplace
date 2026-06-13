"""Environnement de migration Alembic.

Initialise Alembic pour ce service : importe le paquet models afin que chaque
table soit enregistrée sur `Base.metadata` (la cible de l'autogénération/comparaison)
et construit l'URL de base de données depuis les réglages propres de l'app plutôt
que depuis alembic.ini. Alembic appelle `run_migrations_online`/`run_migrations_offline`
selon le mode.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from core.config import settings
from core.database import Base
import models  # noqa: F401 — enregistre tous les modèles sur Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Exécute les migrations en mode hors ligne, en émettant uniquement le SQL vers l'URL.

    Sert à générer des scripts SQL sans se connecter à la base de données.

    Retourne :
        None.
    """
    context.configure(
        url=settings.database.sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en ligne sur une connexion active à la base.

    Ouvre une connexion sans pool depuis l'URL des réglages et applique les
    migrations dans une transaction. C'est le chemin `alembic upgrade` normal.

    Retourne :
        None.
    """
    connectable = create_engine(settings.database.sync_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
