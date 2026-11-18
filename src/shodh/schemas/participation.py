from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ParticipationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contest_id: UUID
    user_id: UUID
    registered_at: datetime


class ParticipantUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr


class ContestParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contest_id: UUID
    user_id: UUID
    registered_at: datetime
    user: ParticipantUserResponse


class ContestParticipantsPageResponse(BaseModel):
    items: list[ContestParticipantResponse]
    total: int
    limit: int
    offset: int
