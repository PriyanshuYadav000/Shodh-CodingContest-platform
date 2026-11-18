from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from shodh.controllers.auth_controller import (
    current_user_controller,
    login_controller,
    register_controller,
)
from shodh.database.session import get_db
from shodh.dependencies.auth import get_current_user
from shodh.models.user import User
from shodh.schemas.auth import RegisterRequest, TokenResponse, UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):

    return register_controller(db, payload)


@router.post(
    "/token",
    response_model=TokenResponse
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    return login_controller(
        db,
        form_data.username,
        form_data.password
    )


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    user: User = Depends(get_current_user)
):

    return current_user_controller(user)