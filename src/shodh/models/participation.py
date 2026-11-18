import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shodh.database.base import Base

if TYPE_CHECKING:
    from shodh.models.contest import Contest
    from shodh.models.user import User


class Participation(Base):
    """A user's registration in one contest.

    The composite primary key makes duplicate registrations impossible even
    when two API workers process the same registration concurrently.
    """

    __tablename__ = "participations"

    __table_args__ = (
        Index(
            "ix_participations_contest_registered_at",
            "contest_id",
            "registered_at",
            "user_id",
        ),
    )

    contest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    contest: Mapped["Contest"] = relationship(back_populates="participations")
    user: Mapped["User"] = relationship(back_populates="participations")
