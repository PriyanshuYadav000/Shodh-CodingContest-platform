import time

from sqlalchemy.exc import SQLAlchemyError

from shodh.database.session import SessionLocal
from shodh.repositories.submission_repository import claim_next_submission
from shodh.services.judge_service import judge_submission

POLL_INTERVAL_SECONDS = 1


def process_one_submission() -> bool:
    with SessionLocal() as db:
        submission = claim_next_submission(db)

        if submission is None:
            return False

        submission_id = submission.id
        attempt = judge_submission(db, submission_id)

        print(
            f"submission_id={submission_id} "
            f"verdict={attempt.verdict.value}"
        )

        return True


def main() -> None:
    while True:
        try:
            processed = process_one_submission()

            if not processed:
                time.sleep(POLL_INTERVAL_SECONDS)

        except SQLAlchemyError as exc:
            print(f"worker_database_error={type(exc).__name__}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
