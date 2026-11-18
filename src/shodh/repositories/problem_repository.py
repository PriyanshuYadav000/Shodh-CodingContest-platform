from uuid import UUID
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from shodh.models.problem import Problem
def create_problem(db:Session,problem:Problem)->Problem:
 db.add(problem);db.flush();return problem
def get_problem(db:Session,contest_id:UUID,problem_id:UUID,for_update:bool=False)->Problem|None:
 q=select(Problem).where(Problem.contest_id==contest_id,Problem.id==problem_id)
 if for_update:q=q.with_for_update()
 return db.scalar(q)
def list_problems(db:Session,contest_id:UUID,include_inactive:bool,limit:int,offset:int):
 q=select(Problem).where(Problem.contest_id==contest_id)
 if not include_inactive:q=q.where(Problem.is_active.is_(True))
 total=db.scalar(select(func.count()).select_from(q.order_by(None).subquery())) or 0
 rows=db.scalars(q.order_by(Problem.created_at,Problem.id).limit(limit).offset(offset)).all()
 return rows,total
