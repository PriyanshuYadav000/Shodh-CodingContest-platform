"""create immutable problem and test-suite versioning

Revision ID: c4d9e7f2a861
Revises: c42f7d1a9001
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d9e7f2a861"
down_revision: Union[str, Sequence[str], None] = "c42f7d1a9001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Upgrade the upstream non-versioned problem rows in place.  Their content
    # is copied into version 1 before legacy mutable columns are removed.
    op.add_column("problems", sa.Column("organization_id", sa.Uuid(), nullable=True))
    op.execute("UPDATE problems p SET organization_id = c.organization_id FROM contests c WHERE c.id = p.contest_id")
    op.alter_column("problems", "organization_id", nullable=False)
    op.create_foreign_key(op.f("fk_problems_organization_id_organizations"), "problems", "organizations", ["organization_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint(op.f("ck_problems_slug_lowercase"), "problems", "slug = lower(slug)")
    op.alter_column("problems", "slug", type_=sa.String(length=120))
    op.create_index("ix_problems_organization_contest_active", "problems", ["organization_id", "contest_id", "is_active"], unique=False)
    op.create_table(
        "problem_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("input_format", sa.Text(), nullable=True),
        sa.Column("output_format", sa.Text(), nullable=True),
        sa.Column("constraints_text", sa.Text(), nullable=True),
        sa.Column("time_limit_ms", sa.Integer(), nullable=False),
        sa.Column("memory_limit_mb", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("memory_limit_mb >= 16 AND memory_limit_mb <= 1024", name=op.f("ck_problem_versions_valid_memory_limit")),
        sa.CheckConstraint("time_limit_ms >= 50 AND time_limit_ms <= 30000", name=op.f("ck_problem_versions_valid_time_limit")),
        sa.CheckConstraint("version_number > 0", name=op.f("ck_problem_versions_positive_version_number")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_problem_versions_created_by_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name=op.f("fk_problem_versions_problem_id_problems"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_problem_versions")),
        sa.UniqueConstraint("problem_id", "version_number", name="uq_problem_versions_problem_version"),
    )
    op.create_index("ix_problem_versions_problem_version", "problem_versions", ["problem_id", "version_number"], unique=False)
    op.execute("""
        INSERT INTO problem_versions (id, problem_id, version_number, title, statement, input_format, output_format, constraints_text, time_limit_ms, memory_limit_mb, created_by)
        SELECT gen_random_uuid(), id, 1, title, statement_md, input_format, output_format, constraints_text, time_limit_ms, memory_limit_mb, created_by
        FROM problems
    """)
    op.create_table(
        "test_suite_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version_number > 0", name=op.f("ck_test_suite_versions_positive_version_number")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_test_suite_versions_created_by_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], name=op.f("fk_test_suite_versions_problem_id_problems"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["problem_version_id"], ["problem_versions.id"], name=op.f("fk_test_suite_versions_problem_version_id_problem_versions"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_suite_versions")),
        sa.UniqueConstraint("problem_id", "version_number", name="uq_test_suite_versions_problem_version"),
        sa.UniqueConstraint("problem_version_id", name="uq_test_suite_versions_problem_version_id"),
    )
    op.create_index("ix_test_suite_versions_problem_version", "test_suite_versions", ["problem_id", "version_number"], unique=False)
    op.execute("""
        INSERT INTO test_suite_versions (id, problem_id, problem_version_id, version_number, created_by)
        SELECT gen_random_uuid(), pv.problem_id, pv.id, 1, pv.created_by
        FROM problem_versions pv WHERE pv.version_number = 1
    """)
    # Keep legacy columns during this forward migration.  The immutable
    # version-1 snapshot is authoritative, while retaining the source fields
    # makes the change recoverable and avoids destructive data loss.
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("test_suite_version_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("ordinal > 0", name=op.f("ck_test_cases_positive_ordinal")),
        sa.ForeignKeyConstraint(["test_suite_version_id"], ["test_suite_versions.id"], name=op.f("fk_test_cases_test_suite_version_id_test_suite_versions"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_cases")),
        sa.UniqueConstraint("test_suite_version_id", "ordinal", name="uq_test_cases_suite_ordinal"),
    )
    op.create_index("ix_test_cases_suite_hidden_ordinal", "test_cases", ["test_suite_version_id", "is_hidden", "ordinal"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_test_cases_suite_hidden_ordinal", table_name="test_cases")
    op.drop_table("test_cases")
    op.drop_index("ix_test_suite_versions_problem_version", table_name="test_suite_versions")
    op.drop_table("test_suite_versions")
    op.drop_index("ix_problem_versions_problem_version", table_name="problem_versions")
    op.drop_table("problem_versions")
    op.drop_index("ix_problems_organization_contest_active", table_name="problems")
    op.drop_constraint(
        op.f("ck_problems_slug_lowercase"), "problems", type_="check"
    )
    op.drop_constraint(
        op.f("fk_problems_organization_id_organizations"),
        "problems",
        type_="foreignkey",
    )
    op.drop_column("problems", "organization_id")
