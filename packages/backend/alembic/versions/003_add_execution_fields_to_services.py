"""add execution fields to services table

Revision ID: 003
Revises: 002
Create Date: 2026-03-31

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute les colonnes de config d'exécution (image/code/ressources) à `services`.

    Note : ces colonnes ont ensuite été supprimées dans la migration 004 une fois la
    config d'exécution déplacée hors de la base marketplace vers le nœud fournisseur.
    """
    op.add_column("services", sa.Column("image", sa.String(512), nullable=True))
    op.add_column("services", sa.Column("code", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("command", sa.String(1024), nullable=True))
    op.add_column("services", sa.Column("default_args", JSONB(), nullable=False, server_default="{}"))
    op.add_column("services", sa.Column("default_env", JSONB(), nullable=False, server_default="{}"))
    op.add_column("services", sa.Column("min_cpu", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("min_gpu", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("min_mem_mb", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    """Supprime les colonnes de config d'exécution ajoutées par cette migration."""
    op.drop_column("services", "retry_count")
    op.drop_column("services", "min_mem_mb")
    op.drop_column("services", "min_gpu")
    op.drop_column("services", "min_cpu")
    op.drop_column("services", "default_env")
    op.drop_column("services", "default_args")
    op.drop_column("services", "command")
    op.drop_column("services", "code")
    op.drop_column("services", "image")
