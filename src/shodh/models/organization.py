import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    func,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shodh.database.base import Base


class Organization(Base):

    __tablename__ = "organizations"

    __table_args__ = (
        UniqueConstraint("slug", name="uq_organizations_slug"),
        CheckConstraint(
            "slug = lower(slug)",
            name="slug_lowercase"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )