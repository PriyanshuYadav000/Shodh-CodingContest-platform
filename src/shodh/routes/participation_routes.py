from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from shodh.controllers.participation_controller import (
    get_my_participation_controller,
    list_contest_participants_controller,
    register_for_contest_controller,
)
from shodh.database.session import get_db
from shodh.dependencies.auth import get_current_user
from shodh.dependencies.organization import require_organization_role
from shodh.models.membership import Membership, MembershipRole
from shodh.models.user import User
from shodh.schemas.participation import (
    ContestParticipantsPageResponse,
    ParticipationResponse,
)

router = APIRouter(tags=["Contest Participation"])


@router.post(
    "/organizations/{organization_id}/contests/{contest_id}/register",
    response_model=ParticipationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_for_contest_route(
    organization_id: UUID,
    contest_id: UUID,
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(
        require_organization_role(MembershipRole.PARTICIPANT)
    ),
    db: Session = Depends(get_db),
):
    return register_for_contest_controller(
        db,
        organization_id,
        contest_id,
        current_user.id,
    )


@router.get(
    "/organizations/{organization_id}/contests/{contest_id}/participation/me",
    response_model=ParticipationResponse,
)
def get_my_participation_route(
    organization_id: UUID,
    contest_id: UUID,
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(
        require_organization_role(MembershipRole.PARTICIPANT)
    ),
    db: Session = Depends(get_db),
):
    return get_my_participation_controller(
        db,
        organization_id,
        contest_id,
        current_user.id,
    )


@router.get(
    "/organizations/{organization_id}/contests/{contest_id}/participants",
    response_model=ContestParticipantsPageResponse,
)
def list_contest_participants_route(
    organization_id: UUID,
    contest_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    membership: Membership = Depends(
        require_organization_role(MembershipRole.ORGANIZER)
    ),
    db: Session = Depends(get_db),
):
    return list_contest_participants_controller(
        db,
        organization_id,
        contest_id,
        limit,
        offset,
    )
