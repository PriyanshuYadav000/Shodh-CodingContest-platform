import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shodh.database.base import Base

if TYPE_CHECKING:
    from shodh.models.contest import Contest
    from shodh.models.organization import Organization


class Problem(Base):
    """Stable identity for a contest problem.

    Mutable state deliberately lives here only when it does not change the
    problem content. Content lives in immutable ``ProblemVersion`` rows.
    """

    __tablename__ = "problems"

    __table_args__ = (
        UniqueConstraint("contest_id", "slug", name="uq_problems_contest_slug"),
        CheckConstraint("slug = lower(slug)", name="slug_lowercase"),
        Index("ix_problems_contest_active", "contest_id", "is_active"),
        Index("ix_problems_organization_contest_active", "organization_id", "contest_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    contest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    # Retained during the forward migration from c42.  Immutable versions are
    # authoritative; these columns keep historical migration data intact.
    legacy_title: Mapped[str] = mapped_column("title", String(180), nullable=False)
    legacy_statement: Mapped[str] = mapped_column("statement_md", Text, nullable=False)
    legacy_input_format: Mapped[str] = mapped_column("input_format", Text, nullable=False)
    legacy_output_format: Mapped[str] = mapped_column("output_format", Text, nullable=False)
    legacy_constraints_text: Mapped[str | None] = mapped_column("constraints_text", Text, nullable=True)
    legacy_time_limit_ms: Mapped[int] = mapped_column("time_limit_ms", Integer, nullable=False)
    legacy_memory_limit_mb: Mapped[int] = mapped_column("memory_limit_mb", Integer, nullable=False)
    legacy_points: Mapped[int] = mapped_column("points", Integer, nullable=False)

    contest: Mapped["Contest"] = relationship(back_populates="problems")
    organization: Mapped["Organization"] = relationship()
    versions: Mapped[list["ProblemVersion"]] = relationship(back_populates="problem", cascade="all, delete-orphan", order_by="ProblemVersion.version_number")


class ProblemVersion(Base):
    __tablename__ = "problem_versions"

    __table_args__ = (
        UniqueConstraint("problem_id", "version_number", name="uq_problem_versions_problem_version"),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint("time_limit_ms >= 50 AND time_limit_ms <= 30000", name="valid_time_limit"),
        CheckConstraint("memory_limit_mb >= 16 AND memory_limit_mb <= 1024", name="valid_memory_limit"),
        Index("ix_problem_versions_problem_version", "problem_id", "version_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    input_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    problem: Mapped[Problem] = relationship(back_populates="versions")
    test_suite_version: Mapped["TestSuiteVersion"] = relationship(back_populates="problem_version", uselist=False, cascade="all, delete-orphan")


class TestSuiteVersion(Base):
    __tablename__ = "test_suite_versions"

    __table_args__ = (
        UniqueConstraint("problem_id", "version_number", name="uq_test_suite_versions_problem_version"),
        UniqueConstraint("problem_version_id", name="uq_test_suite_versions_problem_version_id"),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        Index("ix_test_suite_versions_problem_version", "problem_id", "version_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False)
    problem_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problem_versions.id", ondelete="RESTRICT"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    problem_version: Mapped[ProblemVersion] = relationship(back_populates="test_suite_version")
    test_cases: Mapped[list["TestCase"]] = relationship(back_populates="test_suite_version", cascade="all, delete-orphan", order_by="TestCase.ordinal")


class TestCase(Base):
    __tablename__ = "test_cases"

    __table_args__ = (
        UniqueConstraint("test_suite_version_id", "ordinal", name="uq_test_cases_suite_ordinal"),
        CheckConstraint("ordinal > 0", name="positive_ordinal"),
        Index("ix_test_cases_suite_hidden_ordinal", "test_suite_version_id", "is_hidden", "ordinal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_suite_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_suite_versions.id", ondelete="RESTRICT"), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    test_suite_version: Mapped[TestSuiteVersion] = relationship(back_populates="test_cases")
