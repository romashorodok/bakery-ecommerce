"""create inventory product table

Revision ID: f8eca279b05e
Revises: 623f8d4ed580
Create Date: 2024-07-25 23:23:19.917716

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8eca279b05e"
down_revision: Union[str, None] = "623f8d4ed580"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

table_name = "inventory_products"


def upgrade() -> None:
    op.create_table(
        table_name,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "quantity_in_fridge",
            sa.INT,
            nullable=False,
        ),
        sa.Column(
            "quantity_in_bakery",
            sa.INT,
            nullable=False,
        ),
        sa.Column(
            "quantity_baked",
            sa.INT,
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
