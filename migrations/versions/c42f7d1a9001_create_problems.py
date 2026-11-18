"""Problem tables: initial problem identity and content.
Revision ID: c42f7d1a9001
Revises: a31c7e9b2d10
"""
from alembic import op
import sqlalchemy as sa
revision="c42f7d1a9001";down_revision="a31c7e9b2d10";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("problems",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("contest_id",sa.Uuid(),nullable=False),sa.Column("slug",sa.String(100),nullable=False),sa.Column("title",sa.String(180),nullable=False),sa.Column("statement_md",sa.Text(),nullable=False),sa.Column("input_format",sa.Text(),nullable=False),sa.Column("output_format",sa.Text(),nullable=False),sa.Column("constraints_text",sa.Text()),sa.Column("time_limit_ms",sa.Integer(),nullable=False),sa.Column("memory_limit_mb",sa.Integer(),nullable=False),sa.Column("points",sa.Integer(),nullable=False),sa.Column("created_by",sa.Uuid(),nullable=False),sa.Column("is_active",sa.Boolean(),server_default=sa.true(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["contest_id"],["contests.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["created_by"],["users.id"],ondelete="RESTRICT"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("contest_id","slug",name="uq_problems_contest_slug"))
 op.create_index("ix_problems_contest_active","problems",["contest_id","is_active"])
def downgrade():
 op.drop_index("ix_problems_contest_active",table_name="problems");op.drop_table("problems")
