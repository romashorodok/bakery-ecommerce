"""create user table

Revision ID: ae401e82ba50
Revises: b9282f9755d2
Create Date: 2024-07-26 20:42:54.922216

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ae401e82ba50"
down_revision: Union[str, None] = "b9282f9755d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

table_name = "users"


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
            "first_name",
            sa.VARCHAR(36),
            nullable=False,
        ),
        sa.Column(
            "last_name",
            sa.VARCHAR(36),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.VARCHAR(255),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "hash",
            sa.VARCHAR(60),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
