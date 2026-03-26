"""initial schema — sites, services, invocations

Revision ID: 001
Revises:
Create Date: 2026-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ sites
    op.create_table(
        "sites",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("grpc_endpoint", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("trusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # --------------------------------------------------------------- services
    op.create_table(
        "services",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("provider_site_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("tags", JSONB(), nullable=False, server_default="[]"),
        sa.Column("service_type", sa.String(50), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("price_type", sa.String(50), nullable=False),
        sa.Column("price_amount", sa.Numeric(10, 4), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("visibility", sa.String(50), nullable=False),
        sa.Column("execution_mode", sa.String(50), nullable=False),
        sa.Column("input_schema", JSONB(), nullable=False, server_default="{}"),
        sa.Column("output_schema", JSONB(), nullable=False, server_default="{}"),
        sa.Column("max_concurrency", sa.Integer(), nullable=True),
        sa.Column("timeout_s", sa.Integer(), nullable=True),
        sa.Column("terms_of_use", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["provider_site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_services_slug"),
    )
    op.create_index("ix_services_provider_site_id", "services", ["provider_site_id"])
    op.create_index("ix_services_category", "services", ["category"])
    op.create_index("ix_services_status", "services", ["status"])

    # ------------------------------------------------------------ invocations
    op.create_table(
        "invocations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("service_id", sa.String(36), nullable=False),
        sa.Column("provider_site_id", sa.String(36), nullable=False),
        sa.Column("consumer_site_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("input_payload", JSONB(), nullable=False, server_default="{}"),
        sa.Column("result_payload", JSONB(), nullable=True),
        sa.Column("artifact_uri", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("cost_estimated", sa.Numeric(10, 4), nullable=True),
        sa.Column("cost_final", sa.Numeric(10, 4), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EUR"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.ForeignKeyConstraint(["provider_site_id"], ["sites.id"]),
        sa.ForeignKeyConstraint(["consumer_site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invocations_service_id", "invocations", ["service_id"])
    op.create_index("ix_invocations_consumer_site_id", "invocations", ["consumer_site_id"])
    op.create_index("ix_invocations_status", "invocations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_invocations_status", table_name="invocations")
    op.drop_index("ix_invocations_consumer_site_id", table_name="invocations")
    op.drop_index("ix_invocations_service_id", table_name="invocations")
    op.drop_table("invocations")

    op.drop_index("ix_services_status", table_name="services")
    op.drop_index("ix_services_category", table_name="services")
    op.drop_index("ix_services_provider_site_id", table_name="services")
    op.drop_table("services")

    op.drop_table("sites")
