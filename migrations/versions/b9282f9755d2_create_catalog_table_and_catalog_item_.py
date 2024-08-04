"""create catalog table and catalog item table

Revision ID: b9282f9755d2
Revises: f8eca279b05e
Create Date: 2024-07-26 02:32:24.441664

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

catalog_items = "catalog_items"
catalogs = "catalogs"

revision: str = "b9282f9755d2"
down_revision: Union[str, None] = "f8eca279b05e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ["623f8d4ed580"]


def upgrade() -> None:
    op.create_table(
        catalogs,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "headline",
            sa.Text,
            nullable=False,
        ),
    )

    op.create_table(
        catalog_items,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "visible",
            sa.BOOLEAN,
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "available",
            sa.BOOLEAN,
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "position",
            sa.INT,
        ),
        sa.Column(
            "product_id",
            sa.UUID,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.Column(
            "catalog_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["catalogs.id"]),
        sa.UniqueConstraint("id", "product_id"),
        sa.UniqueConstraint("id", "catalog_id"),
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {catalog_items} CASCADE;")
    op.execute(f"DROP TABLE IF EXISTS {catalogs} CASCADE;")
