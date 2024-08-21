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


def upgrade() -> None:
    op.create_table(
        images,
        sa.Column(
            "id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    pass


def downgrade() -> None:
    pass
