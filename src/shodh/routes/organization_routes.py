from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from shodh.database.session import get_db
from shodh.dependencies.auth import get_current_user
from shodh.dependencies.organization import (
    get_current_organization_membership,
    require_organization_role
)

from shodh.models.user import User
from shodh.models.membership import Membership, MembershipRole

from shodh.schemas.organization import (
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationListItem,
    AddOrganizationMemberRequest,
    OrganizationMemberResponse,
    UpdateMemberRoleRequest
)

from shodh.controllers.organization_controller import (
    create_organization_controller,
    list_organizations_controller,
    get_organization_controller,
    add_member_controller,
    list_members_controller,
    update_member_role_controller
)


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_organization_route(
    payload: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return create_organization_controller(
        db,
        payload,
        current_user
    )


@router.get(
    "",
    response_model=list[OrganizationListItem]
)
def list_organizations_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    return list_organizations_controller(
        db,
        current_user
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse
)
def get_organization_route(
    organization_id: UUID,
    membership: Membership = Depends(
        get_current_organization_membership
    ),
    db: Session = Depends(get_db)
):

    return get_organization_controller(
        db,
        organization_id
    )


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED
)
def add_member_route(
    organization_id: UUID,
    payload: AddOrganizationMemberRequest,
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return add_member_controller(
        db,
        organization_id,
        payload
    )


@router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse]
)
def list_members_route(
    organization_id: UUID,
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return list_members_controller(
        db,
        organization_id
    )


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=OrganizationMemberResponse
)
def update_member_role_route(
    organization_id: UUID,
    user_id: UUID,
    payload: UpdateMemberRoleRequest,
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return update_member_role_controller(
        db,
        organization_id,
        user_id,
        payload
    )