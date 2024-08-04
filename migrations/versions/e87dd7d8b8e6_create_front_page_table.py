"""create front page table

Revision ID: e87dd7d8b8e6
Revises: 9040d03d6539
Create Date: 2024-08-05 20:06:41.268729

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e87dd7d8b8e6"
down_revision: Union[str, None] = "9040d03d6539"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ["b9282f9755d2"]

front_pages = "front_pages"


def upgrade() -> None:
    op.create_table(
        front_pages,
        sa.Column(
            "id",
            sa.BIGINT,
            sa.Identity(increment=1),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "main",
            sa.BOOLEAN,
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "catalog_id",
            sa.UUID,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["catalog_id"], ["catalogs.id"]),
    )
    op.create_index(
        "idx_front_pages_main",
        "front_pages",
        ["main"],
        unique=True,
    )

    op.execute(f"INSERT INTO {front_pages} ( main ) VALUES ( TRUE )")


def downgrade() -> None:
    op.drop_index("idx_front_pages_main", table_name="front_pages")
    op.execute(f"DROP TABLE IF EXISTS {front_pages} CASCADE;")
