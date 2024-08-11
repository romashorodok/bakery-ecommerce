"""create carts and cart items tables

Revision ID: 92342cf042e7
Revises: e87dd7d8b8e6
Create Date: 2024-08-09 21:58:08.759914

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

cart_items = "cart_items"
carts = "carts"

# revision identifiers, used by Alembic.
revision: str = "92342cf042e7"
down_revision: Union[str, None] = "e87dd7d8b8e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ["ae401e82ba50", "623f8d4ed580"]


def upgrade() -> None:
    op.create_table(
        carts,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        f"idx_{carts}_user_id",
        carts,
        ["user_id"],
        unique=False,
    )

    op.create_table(
        cart_items,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "product_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.Column(
            "cart_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
    )


def downgrade() -> None:
    op.drop_index(f"idx_{carts}_user_id", carts)
    op.execute(f"DROP TABLE IF EXISTS {carts} CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {cart_items} CASCADE")
