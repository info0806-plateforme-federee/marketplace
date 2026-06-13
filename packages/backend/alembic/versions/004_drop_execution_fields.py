"""drop execution fields from services table

Revision ID: 004
Revises: 003
Create Date: 2026-04-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Supprime les colonnes de config d'exécution de `services`.

    La config d'exécution (image/code/ressources) vit désormais sur le nœud
    fournisseur et est récupérée/enregistrée via gRPC, donc la marketplace ne la
    stocke plus.
    """
    op.drop_column("services", "retry_count")
    op.drop_column("services", "min_mem_mb")
    op.drop_column("services", "min_gpu")
    op.drop_column("services", "min_cpu")
    op.drop_column("services", "default_env")
    op.drop_column("services", "default_args")
    op.drop_column("services", "command")
    op.drop_column("services", "code")
    op.drop_column("services", "image")


def downgrade() -> None:
    """Réajoute les colonnes de config d'exécution (miroir de la migration 003)."""
    op.add_column("services", sa.Column("image", sa.String(512), nullable=True))
    op.add_column("services", sa.Column("code", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("command", sa.String(1024), nullable=True))
    op.add_column("services", sa.Column("default_args", JSONB(), nullable=False, server_default="{}"))
    op.add_column("services", sa.Column("default_env", JSONB(), nullable=False, server_default="{}"))
    op.add_column("services", sa.Column("min_cpu", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("min_gpu", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("min_mem_mb", sa.Integer(), nullable=True))
    op.add_column("services", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
