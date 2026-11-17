from sqlalchemy.orm import Session

from shodh.models.user import User
from shodh.schemas.auth import RegisterRequest
from shodh.services.auth_service import (register_user,login_user)


def register_controller(
    db: Session,
    payload: RegisterRequest
) -> User:

    return register_user(db, payload)


def login_controller(
    db: Session,
    email: str,
    password: str
) -> dict:

    return login_user(db, email, password)


def current_user_controller(user: User) -> User:

    return user