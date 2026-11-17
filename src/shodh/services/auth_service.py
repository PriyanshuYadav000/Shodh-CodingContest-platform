from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shodh.models.user import User
from shodh.repositories.user_repository import (
    create_user,
    get_user_by_email
)
from shodh.schemas.auth import RegisterRequest
from shodh.security.password import (
    hash_password,
    verify_password
)
from shodh.security.tokens import create_access_token
from shodh.config.settings import settings


def register_user(
    db: Session,
    payload: RegisterRequest
) -> User:

    user = User(
        full_name=payload.full_name,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password)
    )

    try:
        create_user(db, user)
        db.commit()
        db.refresh(user)

        return user

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        ) from exc


def login_user(
    db: Session,
    email: str,
    password: str
) -> dict:

    user = get_user_by_email(db, email.lower())

    if not user or not verify_password(
        password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    token = create_access_token(str(user.id))

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }