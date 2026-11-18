from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from shodh.controllers.submission_controller import (
    create_submission_controller,
    get_submission_controller,
    list_submissions_controller,
    verdict_history_controller,
)
from shodh.database.session import get_db
from shodh.dependencies.auth import get_current_user
from shodh.dependencies.organization import (
    get_current_organization_membership,
    require_organization_role,
)
from shodh.models.membership import Membership, MembershipRole
from shodh.models.user import User
from shodh.schemas.submission import (
    LeaderboardPageResponse,
    SubmissionCreateRequest,
    SubmissionPageResponse,
    SubmissionResponse,
    VerdictResponse,
)
from shodh.services.submission_service import get_leaderboard

router=APIRouter(tags=["Submissions"])
@router.get("/organizations/{organization_id}/contests/{contest_id}/leaderboard",response_model=LeaderboardPageResponse)
def leaderboard(organization_id:UUID,contest_id:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),membership:Membership=Depends(get_current_organization_membership),db:Session=Depends(get_db)): return get_leaderboard(db,organization_id,contest_id,limit,offset)
@router.post("/organizations/{organization_id}/contests/{contest_id}/submissions",response_model=SubmissionResponse,status_code=status.HTTP_201_CREATED)
def create(organization_id:UUID,contest_id:UUID,payload:SubmissionCreateRequest,current_user:User=Depends(get_current_user),membership:Membership=Depends(require_organization_role(MembershipRole.PARTICIPANT)),db:Session=Depends(get_db)): return create_submission_controller(db,organization_id,contest_id,current_user,payload)
@router.get("/organizations/{organization_id}/contests/{contest_id}/submissions",response_model=SubmissionPageResponse)
def listing(organization_id:UUID,contest_id:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),current_user:User=Depends(get_current_user),membership:Membership=Depends(get_current_organization_membership),db:Session=Depends(get_db)): return list_submissions_controller(db,organization_id,contest_id,current_user,membership.role,limit,offset)
@router.get("/organizations/{organization_id}/contests/{contest_id}/submissions/{submission_id}",response_model=SubmissionResponse)
def getone(organization_id:UUID,contest_id:UUID,submission_id:UUID,current_user:User=Depends(get_current_user),membership:Membership=Depends(get_current_organization_membership),db:Session=Depends(get_db)): return get_submission_controller(db,organization_id,contest_id,submission_id,current_user,membership.role)
@router.get("/organizations/{organization_id}/contests/{contest_id}/submissions/{submission_id}/verdicts",response_model=list[VerdictResponse])
def verdicts(organization_id:UUID,contest_id:UUID,submission_id:UUID,current_user:User=Depends(get_current_user),membership:Membership=Depends(get_current_organization_membership),db:Session=Depends(get_db)): return verdict_history_controller(db,organization_id,contest_id,submission_id,current_user,membership.role)
