import re
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator
)

from shodh.models.membership import MembershipRole


class OrganizationCreateRequest(BaseModel):

    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=3, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Organization name is too short")

        return value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = value.strip().lower()

        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError(
                "Slug must contain lowercase letters, numbers and hyphens"
            )

        return value


class OrganizationResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class OrganizationListItem(OrganizationResponse):

    role: MembershipRole


class AddOrganizationMemberRequest(BaseModel):

    email: EmailStr
    role: MembershipRole = MembershipRole.PARTICIPANT

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class MemberUserResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool


class OrganizationMemberResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    user_id: UUID
    role: MembershipRole
    created_at: datetime
    user: MemberUserResponse


class UpdateMemberRoleRequest(BaseModel):

    role: MembershipRole