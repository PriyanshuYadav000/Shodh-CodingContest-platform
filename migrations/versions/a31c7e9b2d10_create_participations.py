"""create contest participations

Revision ID: a31c7e9b2d10
Revises: 770a782ea04e
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a31c7e9b2d10"
down_revision: Union[str, Sequence[str], None] = "770a782ea04e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "participations",
        sa.Column("contest_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["contest_id"],
            ["contests.id"],
            name=op.f("fk_participations_contest_id_contests"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_participations_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "contest_id",
            "user_id",
            name=op.f("pk_participations"),
        ),
    )
    op.create_index(
        "ix_participations_contest_registered_at",
        "participations",
        ["contest_id", "registered_at", "user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_participations_contest_registered_at",
        table_name="participations",
    )
    op.drop_table("participations")
