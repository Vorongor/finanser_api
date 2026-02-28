from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.database.models import UserModel
from src.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    UserNotFound,
    LoggedOutError,
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

    result = await db.execute(
        select(UserModel)
        .where(UserModel.id == user_id)
        # .options(joinedload(UserModel.refresh_tokens))
    )
    auth_user = result.unique().scalar_one_or_none()

    if not auth_user:
        raise UserNotFound()

    # if not auth_user.refresh_tokens:
    #     raise LoggedOutError()

    return AuthUserSchema(
        id=auth_user.id,
        email=auth_user.email,
        is_active=auth_user.is_active,
    )
