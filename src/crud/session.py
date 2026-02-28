from sqlalchemy.ext.asyncio import AsyncSession

from .user import retrieve_user_by_email
from src.schemas import (
    LoginRequestSchema,
    LoginResponseSchema
)
from src.exceptions import (
    IncorrectCredentialsError,
    UserEmailNotConfirmed,
)
from src.security.interfaces import JWTAuthManagerInterface


async def login_user(
        user_data: LoginRequestSchema,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
) -> LoginResponseSchema:
    user = await retrieve_user_by_email(db=db, email=user_data.email)
    if not user or not user.check_password(user_data.password):
        raise IncorrectCredentialsError()

    if not user.is_active:
        raise UserEmailNotConfirmed()

    token_data = {
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active,
    }

    access_token = jwt_manager.create_access_token(data=token_data)
    # TODO Save refresh token
    refresh_token = jwt_manager.create_refresh_token(data=token_data)

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
