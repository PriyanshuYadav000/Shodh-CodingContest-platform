"""Add explicit worker lifecycle states to submissions.

Revision ID: f3a8b2d9c610
Revises: e6f1c4b8d923
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a8b2d9c610"
down_revision: Union[str, Sequence[str], None] = "e6f1c4b8d923"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "submissions",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    bind = op.get_bind()
    checks = sa.inspect(bind).get_check_constraints("submissions")
    for check in checks:
        sqltext = (check.get("sqltext") or "").lower()
        if "status" in sqltext and check.get("name"):
            op.drop_constraint(check["name"], "submissions", type_="check")

    # Preserve existing judged rows as completed rows.
    op.execute(
        "UPDATE submissions SET status = 'completed' WHERE status = 'judged'"
    )
    op.create_check_constraint(
        op.f("ck_submissions_submission_status"),
        "submissions",
        "status IN ('queued', 'running', 'completed', 'failed')",
    )

    indexes = {
        index["name"] for index in sa.inspect(bind).get_indexes("submissions")
    }
    if "ix_submissions_status_created" not in indexes:
        op.create_index(
            "ix_submissions_status_created",
            "submissions",
            ["status", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        "ix_submissions_status_created",
        table_name="submissions",
    )
    op.drop_constraint(
        op.f("ck_submissions_submission_status"),
        "submissions",
        type_="check",
    )
    op.execute(
        "UPDATE submissions SET status = 'judged' "
        "WHERE status IN ('running', 'completed', 'failed')"
    )
    op.create_check_constraint(
        op.f("ck_submissions_submission_status"),
        "submissions",
        "status IN ('queued', 'judged')",
    )
    op.drop_column("submissions", "completed_at")
    op.drop_column("submissions", "started_at")
