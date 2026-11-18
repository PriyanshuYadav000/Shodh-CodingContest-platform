"""Claim one queued submission and print its identifier.

The execution/judging step is added in the next Stage 2 checkpoint.
"""

from shodh.database.session import SessionLocal
from shodh.repositories.submission_repository import claim_next_submission


def main() -> None:
    with SessionLocal() as db:
        submission = claim_next_submission(db)

    if submission is None:
        print("no_queued_submissions")
        return

    print(f"claimed_submission_id={submission.id}")


if __name__ == "__main__":
    main()
