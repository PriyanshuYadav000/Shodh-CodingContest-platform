from shodh.services.submission_service import (
    create_new_submission,
    get_submissions,
    get_verdict_history,
    get_visible_submission,
)


def create_submission_controller(db,org,contest,user,payload): return create_new_submission(db,org,contest,user.id,payload)
def list_submissions_controller(db,org,contest,user,role,limit,offset): return get_submissions(db,org,contest,user.id,role,limit,offset)
def get_submission_controller(db,org,contest,sid,user,role): return get_visible_submission(db,org,contest,sid,user.id,role)
def verdict_history_controller(db,org,contest,sid,user,role): return get_verdict_history(db,org,contest,sid,user.id,role)
