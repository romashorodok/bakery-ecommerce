"""create order table

Revision ID: ee8ddc35d5bc
Revises: 92342cf042e7
Create Date: 2024-08-17 01:12:05.290722

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from bakery_ecommerce.internal.order.store.order_model import (
    Order_Status_Enum,
    Payment_Provider_Enum,
)


# revision identifiers, used by Alembic.
revision: str = "ee8ddc35d5bc"
down_revision: Union[str, None] = "92342cf042e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ["92342cf042e7"]

orders = "orders"
order_items = "order_items"
payment_details = "payment_details"


def upgrade() -> None:
    order_status_enum = postgresql.ENUM(Order_Status_Enum, name="order_status_enum")
    payment_provider_enum = postgresql.ENUM(
        Payment_Provider_Enum, name="payment_provider_enum"
    )

    op.create_table(
        payment_details,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "payment_provider",
            payment_provider_enum,
            nullable=True,
        ),
    )

    op.create_table(
        orders,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "order_status",
            order_status_enum,
            nullable=False,
            server_default=sa.text(f"'{Order_Status_Enum.DRAFT}'::order_status_enum"),
        ),
        sa.Column(
            "payment_detail_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["payment_detail_id"], ["payment_details.id"]),
        sa.Column(
            "user_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        order_items,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "price",
            sa.Integer,
            nullable=False,
        ),
        sa.Column(
            "price_multiplier",
            sa.Integer,
            nullable=False,
        ),
        sa.Column(
            "price_multiplied",
            sa.Integer,
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "order_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.Column(
            "product_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )


def downgrade() -> None:
    op.execute("DROP TYPE IF EXISTS order_status_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS payment_provider_enum CASCADE")

    op.execute(f"DROP TABLE IF EXISTS {order_items} CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {payment_details} CASCADE")
    op.execute(f"DROP TABLE IF EXISTS {orders} CASCADE")
