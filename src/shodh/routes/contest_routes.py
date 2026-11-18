from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from shodh.database.session import get_db
from shodh.dependencies.organization import (
    get_current_organization_membership,
    require_organization_role
)

from shodh.models.user import User
from shodh.models.membership import Membership, MembershipRole

from shodh.dependencies.auth import get_current_user

from shodh.schemas.contest import (
    ContestCreateRequest,
    ContestUpdateRequest,
    ContestResponse,
    ContestPageResponse
)

from shodh.controllers.contest_controller import (
    create_contest_controller,
    list_contests_controller,
    get_contest_controller,
    update_contest_controller,
    publish_contest_controller,
    cancel_contest_controller
)


router = APIRouter(
    tags=["Contests"]
)


@router.post(
    "/organizations/{organization_id}/contests",
    response_model=ContestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_contest_route(
    organization_id: UUID,
    payload: ContestCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return create_contest_controller(
        db,
        organization_id,
        payload,
        current_user
    )


@router.get(
    "/organizations/{organization_id}/contests",
    response_model=ContestPageResponse
)
def list_contests_route(
    organization_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    membership: Membership = Depends(
        get_current_organization_membership
    ),
    db: Session = Depends(get_db)
):

    return list_contests_controller(
        db,
        organization_id,
        membership.role,
        limit,
        offset
    )


@router.get(
    "/organizations/{organization_id}/contests/{contest_id}",
    response_model=ContestResponse
)
def get_contest_route(
    organization_id: UUID,
    contest_id: UUID,
    membership: Membership = Depends(
        get_current_organization_membership
    ),
    db: Session = Depends(get_db)
):

    return get_contest_controller(
        db,
        organization_id,
        contest_id
    )


@router.patch(
    "/organizations/{organization_id}/contests/{contest_id}",
    response_model=ContestResponse
)
def update_contest_route(
    organization_id: UUID,
    contest_id: UUID,
    payload: ContestUpdateRequest,
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return update_contest_controller(
        db,
        organization_id,
        contest_id,
        payload
    )


@router.post(
    "/organizations/{organization_id}/contests/{contest_id}/publish",
    response_model=ContestResponse
)
def publish_contest_route(
    organization_id: UUID,
    contest_id: UUID,
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return publish_contest_controller(
        db,
        organization_id,
        contest_id
    )


@router.post(
    "/organizations/{organization_id}/contests/{contest_id}/cancel",
    response_model=ContestResponse
)
def cancel_contest_route(
    organization_id: UUID,
    contest_id: UUID,
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db)
):

    return cancel_contest_controller(
        db,
        organization_id,
        contest_id
    )