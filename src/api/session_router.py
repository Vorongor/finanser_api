from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import get_jwt_manager
from src.crud import login_user, logout_user, refresh_user_token
from src.database import get_db
from src.schemas import (
    LoginResponseSchema,
    LoginRequestSchema,
    AuthUserSchema,
    LogoutResponseSchema,
    RefreshSchema,
)
from src.security.interfaces import JWTAuthManagerInterface

from src.exceptions import (
    IncorrectCredentialsError,
    UserEmailNotConfirmed,
    TokenExpiredError,
    InvalidTokenError,
    LoggedOutError,
)
from src.security.utils import get_current_user

session_router = APIRouter(prefix="/session", tags=["Session"])


@session_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponseSchema,
    summary="Login a user, returns tokens",
)
async def login(
    login_data: LoginRequestSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
):
    try:
        return await login_user(
            user_data=login_data, db=db, jwt_manager=jwt_manager
        )
    except IncorrectCredentialsError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.details,
        )
    except UserEmailNotConfirmed as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.details,
        )


@session_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=LogoutResponseSchema,
)
async def logout(
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponseSchema:
    try:
        message = await logout_user(user_data=auth_user, db=db)
        return LogoutResponseSchema(message=message)
    except IncorrectCredentialsError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.details,
        )


@session_router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=RefreshSchema,
)
async def refresh(
    refresh_data: RefreshSchema,
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> RefreshSchema:
    try:
        return await refresh_user_token(
            refresh_data=refresh_data, jwt_manager=jwt_manager
        )
    except (TokenExpiredError, InvalidTokenError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err.details,
        )
