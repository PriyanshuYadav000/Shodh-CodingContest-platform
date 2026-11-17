from sqlalchemy import select
from sqlalchemy.orm import Session

from shodh.models.user import User


def get_user_by_email(
    db: Session,
    email: str
) -> User | None:

    statement = select(User).where(
        User.email == email.lower()
    )

    return db.scalar(statement)


def get_user_by_id(
    db: Session,
    user_id
) -> User | None:

    return db.get(User, user_id)


def create_user(
    db: Session,
    user: User
) -> User:

    db.add(user)
    db.flush()

    return user