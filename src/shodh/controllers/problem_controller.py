from uuid import UUID
from sqlalchemy.orm import Session
from shodh.models.membership import MembershipRole
from shodh.models.user import User
from shodh.schemas.problem import ProblemCreateRequest
from shodh.services.problem_service import create_problem_for_contest,get_problem_details,list_contest_problems,update_problem_active
def create_problem_controller(db:Session,org:UUID,contest:UUID,user:User,payload:ProblemCreateRequest):
 return create_problem_for_contest(db,org,contest,user.id,payload)
def list_problems_controller(db,org,contest,role,limit,offset):
 return list_contest_problems(db,org,contest,role,limit,offset)
def get_problem_controller(db,org,contest,pid,role):
 return get_problem_details(db,org,contest,pid,role)
def update_problem_controller(db,org,contest,pid,active):
 return update_problem_active(db,org,contest,pid,active)
