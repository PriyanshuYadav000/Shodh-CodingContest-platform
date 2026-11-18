from uuid import UUID
from fastapi import APIRouter,Depends,Query,status
from sqlalchemy.orm import Session
from shodh.controllers.problem_controller import create_problem_controller,get_problem_controller,list_problems_controller,update_problem_controller
from shodh.database.session import get_db
from shodh.dependencies.auth import get_current_user
from shodh.dependencies.organization import get_current_organization_membership,require_organization_role
from shodh.models.membership import Membership,MembershipRole
from shodh.models.user import User
from shodh.schemas.problem import ProblemCreateRequest,ProblemPageResponse,ProblemResponse,ProblemUpdateRequest
router=APIRouter(tags=["Problems"])
@router.post("/organizations/{organization_id}/contests/{contest_id}/problems",response_model=ProblemResponse,status_code=status.HTTP_201_CREATED)
def create_problem_route(organization_id:UUID,contest_id:UUID,payload:ProblemCreateRequest,current_user:User=Depends(get_current_user),membership:Membership=Depends(require_organization_role(MembershipRole.ORGANIZER)),db:Session=Depends(get_db)):
 return create_problem_controller(db,organization_id,contest_id,current_user,payload)
@router.get("/organizations/{organization_id}/contests/{contest_id}/problems",response_model=ProblemPageResponse)
def list_problems_route(organization_id:UUID,contest_id:UUID,limit:int=Query(20,ge=1,le=100),offset:int=Query(0,ge=0),membership:Membership=Depends(get_current_organization_membership),db:Session=Depends(get_db)):
 return list_problems_controller(db,organization_id,contest_id,membership.role,limit,offset)
@router.get("/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}",response_model=ProblemResponse)
def get_problem_route(organization_id:UUID,contest_id:UUID,problem_id:UUID,membership:Membership=Depends(get_current_organization_membership),db:Session=Depends(get_db)):
 return get_problem_controller(db,organization_id,contest_id,problem_id,membership.role)
@router.patch("/organizations/{organization_id}/contests/{contest_id}/problems/{problem_id}",response_model=ProblemResponse)
def patch_problem_route(organization_id:UUID,contest_id:UUID,problem_id:UUID,payload:ProblemUpdateRequest,membership:Membership=Depends(require_organization_role(MembershipRole.ORGANIZER)),db:Session=Depends(get_db)):
 if payload.is_active is None:return get_problem_controller(db,organization_id,contest_id,problem_id,MembershipRole.ORGANIZER)
 return update_problem_controller(db,organization_id,contest_id,problem_id,payload.is_active)
