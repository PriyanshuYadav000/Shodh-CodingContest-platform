import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
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
    from shodh.models.participation import Participation\n    from shodh.models.problem import Problem
    from shodh.models.problem import Problem


class ContestStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Contest(Base):
    __tablename__ = "contests"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "slug",
            name="uq_contests_organization_slug",
        ),
        CheckConstraint(
            "registration_opens_at < starts_at",
            name="registration_before_start",
        ),
        CheckConstraint(
            "starts_at < ends_at",
            name="start_before_end",
        ),
        CheckConstraint(
            "wrong_attempt_penalty_minutes >= 0",
            name="nonnegative_penalty",
        ),
        Index(
            "ix_contests_organization_status",
            "organization_id",
            "status",
        ),
        Index(
            "ix_contests_start_end",
            "starts_at",
            "ends_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ContestStatus] = mapped_column(
        Enum(
            ContestStatus,
            name="contest_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=ContestStatus.DRAFT,
        nullable=False,
    )
    registration_opens_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    wrong_attempt_penalty_minutes: Mapped[int] = mapped_column(
        Integer,
        default=20,
        server_default="20",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    problems: Mapped[list["Problem"]] = relationship(back_populates="contest", cascade="all, delete-orphan")

    participations: Mapped[list["Participation"]] = relationship(
        back_populates="contest",
        cascade="all, delete-orphan",
    )
