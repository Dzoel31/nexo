"""add_classification_fields_to_scheduled_events

Revision ID: 6c8f391b4a92
Revises: 2faacb1e41c6
Create Date: 2026-09-02 22:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c8f391b4a92"
down_revision: Union[str, Sequence[str], None] = "2faacb1e41c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "scheduled_events",
        sa.Column("classification_label", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "scheduled_events",
        sa.Column(
            "is_discord_event",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_index(
        op.f("ix_scheduled_events_classification_label"),
        "scheduled_events",
        ["classification_label"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_scheduled_events_classification_label"),
        table_name="scheduled_events",
    )
    op.drop_column("scheduled_events", "is_discord_event")
    op.drop_column("scheduled_events", "classification_label")
