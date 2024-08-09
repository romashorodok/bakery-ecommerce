"""create product table

Revision ID: 623f8d4ed580
Revises:
Create Date: 2024-07-24 22:24:16.396364

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "623f8d4ed580"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

table_name = "products"


def upgrade() -> None:
    op.create_table(
        table_name,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "name",
            sa.VARCHAR(30),
            nullable=False,
        ),
        sa.Column(
            "price",
            sa.Integer,
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
