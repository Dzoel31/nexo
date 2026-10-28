"""scope conversations by user and channel

Revision ID: d47a2c18b903
Revises: 4af8bb7f117f
Create Date: 2026-10-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d47a2c18b903"
down_revision: str | Sequence[str] | None = "4af8bb7f117f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_conversations_user_channel",
        "conversations",
        ["user_id", "channel_id"],
    )
    op.create_index(
        "uq_conversations_user_channel_null",
        "conversations",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("channel_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_conversations_user_channel_null", table_name="conversations")
    op.drop_constraint("uq_conversations_user_channel", "conversations", type_="unique")
