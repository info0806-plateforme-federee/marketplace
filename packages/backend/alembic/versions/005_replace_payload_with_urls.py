"""Replace result_payload and artifact_uri with presigned URL columns.

Marketplace no longer stores output data for confidentiality compliance.
Results are fetched directly from the provider's S3 via presigned URLs.

Revision ID: 005
Revises: 004
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remplace les données de résultat stockées par des colonnes d'URL présignées.

    Supprime `result_payload`/`artifact_uri` et ajoute `result_url`/`artifact_url` ;
    les sorties sont désormais récupérées depuis le S3 du fournisseur au lieu d'être
    stockées ici.
    """
    op.add_column("invocations", sa.Column("result_url", sa.String(2048), nullable=True))
    op.add_column("invocations", sa.Column("artifact_url", sa.String(2048), nullable=True))
    op.drop_column("invocations", "result_payload")
    op.drop_column("invocations", "artifact_uri")


def downgrade() -> None:
    """Restaure les colonnes de payload stocké et supprime les colonnes d'URL."""
    op.add_column("invocations", sa.Column("artifact_uri", sa.String(500), nullable=True))
    op.add_column(
        "invocations",
        sa.Column("result_payload", sa.dialects.postgresql.JSONB(), nullable=True),
    )
    op.drop_column("invocations", "artifact_url")
    op.drop_column("invocations", "result_url")
