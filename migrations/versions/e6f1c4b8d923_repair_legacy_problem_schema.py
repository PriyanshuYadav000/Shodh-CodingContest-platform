"""repair legacy problem columns on pre-reconciliation databases"""

from alembic import op
import sqlalchemy as sa

revision = "e6f1c4b8d923"
down_revision = "d5e8f3a9b712"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Older local databases applied the original versioning migration before
    # c42 was reconciled. Recreate the retained legacy fields from version 1.
    columns = (
        ("title", sa.String(180)), ("statement_md", sa.Text()),
        ("input_format", sa.Text()), ("output_format", sa.Text()),
        ("constraints_text", sa.Text()), ("time_limit_ms", sa.Integer()),
        ("memory_limit_mb", sa.Integer()), ("points", sa.Integer()),
    )
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("problems")}
    missing = [(name, column_type) for name, column_type in columns if name not in existing]
    for name, column_type in missing:
        op.add_column("problems", sa.Column(name, column_type, nullable=True))
    op.execute("""
        UPDATE problems p SET title = pv.title, statement_md = pv.statement,
        input_format = COALESCE(pv.input_format, ''), output_format = COALESCE(pv.output_format, ''),
        constraints_text = pv.constraints_text, time_limit_ms = pv.time_limit_ms,
        memory_limit_mb = pv.memory_limit_mb, points = 100
        FROM problem_versions pv
        WHERE pv.problem_id = p.id AND pv.version_number = 1
    """)
    for name in ("title", "statement_md", "input_format", "output_format", "time_limit_ms", "memory_limit_mb", "points"):
        if name in {name for name, _ in missing}:
            op.alter_column("problems", name, nullable=False)
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("problems")}
    if "ix_problems_contest_active" not in indexes:
        op.create_index("ix_problems_contest_active", "problems", ["contest_id", "is_active"])
    op.drop_constraint("fk_problems_contest_id_contests", "problems", type_="foreignkey")
    op.create_foreign_key("fk_problems_contest_id_contests", "problems", "contests", ["contest_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint("fk_problems_contest_id_contests", "problems", type_="foreignkey")
    op.create_foreign_key("fk_problems_contest_id_contests", "problems", "contests", ["contest_id"], ["id"], ondelete="RESTRICT")
    op.drop_index("ix_problems_contest_active", table_name="problems")
    for name in ("points", "memory_limit_mb", "time_limit_ms", "constraints_text", "output_format", "input_format", "statement_md", "title"):
        op.drop_column("problems", name)
