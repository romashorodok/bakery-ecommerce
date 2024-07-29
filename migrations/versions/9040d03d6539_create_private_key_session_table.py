"""create private key session table

Revision ID: 9040d03d6539
Revises: ae401e82ba50
Create Date: 2024-07-29 18:27:09.376524

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "9040d03d6539"
down_revision: Union[str, None] = "ae401e82ba50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ["ae401e82ba50"]


table_name = "private_key_sessions"


def upgrade() -> None:
    op.create_table(
        table_name,
        sa.Column(
            "id",
            sa.BIGINT,
            sa.Identity(increment=1),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "kid",
            sa.Text,
            nullable=False,
        ),
        sa.Column(
            "signature",
            JSONB,
            nullable=False,
        ),
        sa.Column(
            "blacklisted",
            sa.BOOLEAN,
            nullable=False,
            server_default="False",
        ),
        sa.Column(
            "user_id",
            sa.UUID,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(
        "idx_private_key_sessions_kid",
        "private_key_sessions",
        ["kid"],
        unique=True,
    )
    op.create_index(
        "idx_private_key_sessions_user_id",
        "private_key_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_private_key_sessions_kid", table_name="private_key_sessions")
    op.drop_index("idx_private_key_sessions_user_id", table_name="private_key_sessions")
    op.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
