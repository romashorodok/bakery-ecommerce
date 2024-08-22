"""create image table

Revision ID: 6dba110440f9
Revises: ee8ddc35d5bc
Create Date: 2024-08-21 13:47:27.625200

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6dba110440f9"
down_revision: Union[str, None] = "ee8ddc35d5bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ["623f8d4ed580"]

images = "images"
product_images = "product_images"


def upgrade() -> None:
    op.create_table(
        images,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "original_file",
            sa.Text,
            nullable=False,
        ),
        sa.Column(
            "original_file_hash",
            sa.Text,
            nullable=False,
        ),
        sa.Column(
            "bucket",
            sa.Text,
            nullable=False,
        ),
        sa.Column(
            "transcoded_file",
            sa.Text,
            nullable=True,
        ),
        sa.Column(
            "transcoded_file_mime",
            sa.Text,
            nullable=True,
        ),
    )

    op.create_table(
        product_images,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("product_id", sa.UUID, nullable=False),
        sa.Column("image_id", sa.UUID, nullable=False),
        sa.Column(
            "featured",
            sa.Boolean,
            nullable=False,
            server_default="False",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"]),
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {images} CASCADE;")
    op.execute(f"DROP TABLE IF EXISTS {product_images} CASCADE;")
