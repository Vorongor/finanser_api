from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models import RefreshTokenModel
from src.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    LoggedOutError,
    UserEmailNotConfirmed,
)
from src.schemas import AuthUserSchema
from src.security.interfaces import JWTAuthManagerInterface
from src.config.dependencies import get_jwt_manager

security_scheme = HTTPBearer()


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> AuthUserSchema:
    token = auth.credentials
    try:
        user_data = jwt_manager.decode_access_token(token)

    except (TokenExpiredError, InvalidTokenError):
        raise

    user_id = user_data.get("user_id")
    session_id = user_data.get("session_id")
    email = user_data.get("email")
    is_active = user_data.get("is_active")

    if not user_id or not session_id or not email:
        raise InvalidTokenError(
            details="Invalid token credentials, please log in again.",
        )

    if not is_active:
        raise UserEmailNotConfirmed()

    result = await db.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.session_id == session_id,
        )
    )
    auth_user_token = result.unique().scalar_one_or_none()

    if not auth_user_token:
        raise LoggedOutError()

    return AuthUserSchema(
        id=user_id,
        email=email,
        is_active=is_active,
        session_id=session_id,
    )
