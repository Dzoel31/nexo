"""create_token_usage_logs_table

Revision ID: e73682910301
Revises: 32629ef3fa73
Create Date: 2026-09-01 09:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e73682910301"
down_revision: Union[str, Sequence[str], None] = "32629ef3fa73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add token_count column to messages table
    op.add_column(
        "messages",
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # 2. Create token_usage_logs table
    op.create_table(
        "token_usage_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "completion_tokens",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_token_usage_logs_guild_id"),
        "token_usage_logs",
        ["guild_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_token_usage_logs_user_id"),
        "token_usage_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_token_usage_logs_user_id"), table_name="token_usage_logs")
    op.drop_index(op.f("ix_token_usage_logs_guild_id"), table_name="token_usage_logs")
    op.drop_table("token_usage_logs")
    op.drop_column("messages", "token_count")
