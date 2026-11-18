import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean,DateTime,ForeignKey,Index,String,Text,Uuid,UniqueConstraint,func
from sqlalchemy.orm import Mapped,mapped_column,relationship
from shodh.database.base import Base
if TYPE_CHECKING:
 from shodh.models.contest import Contest
class Problem(Base):
 __tablename__="problems"
 __table_args__=(UniqueConstraint("contest_id","slug",name="uq_problems_contest_slug"),Index("ix_problems_contest_active","contest_id","is_active"))
 id:Mapped[uuid.UUID]=mapped_column(Uuid(as_uuid=True),primary_key=True,default=uuid.uuid4)
 contest_id:Mapped[uuid.UUID]=mapped_column(ForeignKey("contests.id",ondelete="CASCADE"),nullable=False)
 slug:Mapped[str]=mapped_column(String(100),nullable=False)
 title:Mapped[str]=mapped_column(String(180),nullable=False)
 statement_md:Mapped[str]=mapped_column(Text,nullable=False)
 input_format:Mapped[str]=mapped_column(Text,nullable=False)
 output_format:Mapped[str]=mapped_column(Text,nullable=False)
 constraints_text:Mapped[str|None]=mapped_column(Text)
 time_limit_ms:Mapped[int]=mapped_column(default=2000,nullable=False)
 memory_limit_mb:Mapped[int]=mapped_column(default=256,nullable=False)
 points:Mapped[int]=mapped_column(default=100,nullable=False)
 created_by:Mapped[uuid.UUID]=mapped_column(ForeignKey("users.id",ondelete="RESTRICT"),nullable=False)
 is_active:Mapped[bool]=mapped_column(Boolean,default=True,server_default="true",nullable=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 contest:Mapped["Contest"]=relationship(back_populates="problems")
