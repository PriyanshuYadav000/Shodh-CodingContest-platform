import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shodh.database.base import Base


class MembershipRole(str, enum.Enum):

    ORGANIZER = "organizer"
    PARTICIPANT = "participant"


class Membership(Base):

    __tablename__ = "memberships"

    __table_args__ = (
        Index("ix_memberships_user_id", "user_id"),
        Index(
            "ix_memberships_organization_role",
            "organization_id",
            "role"
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            MembershipRole,
            name="membership_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True
        ),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="memberships"
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="memberships"
    )