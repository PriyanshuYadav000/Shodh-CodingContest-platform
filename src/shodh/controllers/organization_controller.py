from uuid import UUID

from sqlalchemy.orm import Session

from shodh.models.user import User

from shodh.schemas.organization import (
    OrganizationCreateRequest,
    AddOrganizationMemberRequest,
    UpdateMemberRoleRequest
)

from shodh.services.organization_service import (
    create_organization,
    get_user_organizations,
    get_organization,
    add_organization_member,
    get_organization_members,
    update_member_role
)


def create_organization_controller(
    db: Session,
    payload: OrganizationCreateRequest,
    current_user: User
):
    return create_organization(
        db,
        payload,
        current_user.id
    )


def list_organizations_controller(
    db: Session,
    current_user: User
):
    return get_user_organizations(db, current_user.id)


def get_organization_controller(
    db: Session,
    organization_id: UUID
):
    return get_organization(db, organization_id)


def add_member_controller(
    db: Session,
    organization_id: UUID,
    payload: AddOrganizationMemberRequest
):
    return add_organization_member(
        db,
        organization_id,
        payload
    )


def list_members_controller(
    db: Session,
    organization_id: UUID
):
    return get_organization_members(
        db,
        organization_id
    )


def update_member_role_controller(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    payload: UpdateMemberRoleRequest
):
    return update_member_role(
        db,
        organization_id,
        user_id,
        payload
    )