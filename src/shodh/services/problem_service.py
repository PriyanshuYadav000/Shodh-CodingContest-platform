from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from shodh.models.contest import ContestStatus
from shodh.models.membership import MembershipRole
from shodh.models.problem import Problem
from shodh.repositories.contest_repository import get_contest_by_id
from shodh.repositories.problem_repository import create_problem,get_problem,list_problems
from shodh.schemas.problem import ProblemCreateRequest
def check_contest(db,org,contest,role):
 c=get_contest_by_id(db,org,contest)
 if c is None or(role==MembershipRole.PARTICIPANT and c.status!=ContestStatus.PUBLISHED):raise HTTPException(404,"Contest not found")
 return c
def create_problem_for_contest(db:Session,org:UUID,contest:UUID,creator:UUID,payload:ProblemCreateRequest):
 check_contest(db,org,contest,MembershipRole.ORGANIZER)
 p=Problem(contest_id=contest,created_by=creator,**payload.model_dump())
 try:
  create_problem(db,p);db.commit();db.refresh(p);return p
 except IntegrityError as e:
  db.rollback();raise HTTPException(409,"Problem slug already exists in this contest")from e
def list_contest_problems(db,org,contest,role,limit,offset):
 check_contest(db,org,contest,role)
 rows,total=list_problems(db,contest,role==MembershipRole.ORGANIZER,limit,offset)
 return {"items":rows,"total":total,"limit":limit,"offset":offset}
def get_problem_details(db,org,contest,pid,role):
 check_contest(db,org,contest,role)
 p=get_problem(db,contest,pid)
 if p is None or(role==MembershipRole.PARTICIPANT and not p.is_active):raise HTTPException(404,"Problem not found")
 return p
def update_problem_active(db,org,contest,pid,active):
 check_contest(db,org,contest,MembershipRole.ORGANIZER)
 p=get_problem(db,contest,pid,True)
 if p is None:raise HTTPException(404,"Problem not found")
 p.is_active=active;db.commit();db.refresh(p);return p
