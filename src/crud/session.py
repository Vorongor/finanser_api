from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .user import retrieve_user_by_email
from src.schemas import (
    LoginRequestSchema,
    LoginResponseSchema, AuthUserSchema, RefreshSchema
)
from src.exceptions import (
    IncorrectCredentialsError,
    UserEmailNotConfirmed,
)
from src.security.interfaces import JWTAuthManagerInterface
from src.config import get_settings
from src.database.models import RefreshTokenModel, UserModel

settings = get_settings()


async def login_user(
        user_data: LoginRequestSchema,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
) -> LoginResponseSchema:
    """
    Crud function for login user. Create new session and save it to db
    Parameters:
        user_data (LoginRequestSchema): email and password
    Returns:
        LoginResponseSchema: pair access token and refresh token for
        current session
    """
    user = await retrieve_user_by_email(db=db, email=user_data.email)
    if not user or not user.check_password(user_data.password):
        raise IncorrectCredentialsError()

    if not user.is_active:
        raise UserEmailNotConfirmed()
    session_id = str(uuid4())

    token_data = {
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "session_id": session_id,
    }

    access_token = jwt_manager.create_access_token(data=token_data)
    refresh_token = jwt_manager.create_refresh_token(data=token_data)

    db_token = RefreshTokenModel.create(
        user_id=user.id,
        token=refresh_token,
        days_valid=settings.REFRESH_TOKEN_DAYS,
        session_id=session_id
    )
    db.add(db_token)
    try:
        await db.commit()
    except IntegrityError:
        raise IncorrectCredentialsError(
            details="Unable to log in with provided credentials",
        )

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def logout_user(
        user_data: AuthUserSchema,
        db: AsyncSession,
) -> str:
    """
    Crud function for logout user and remove session id from db
    Parameters:
        user_data (AuthUserSchema): access token
    Returns:
        str: message about logged out user
    """
    stmt = delete(RefreshTokenModel).where(
        RefreshTokenModel.user_id == user_data.id,
        RefreshTokenModel.session_id == user_data.session_id
    )

    result = await db.execute(stmt)

    if result.rowcount == 0:
        raise IncorrectCredentialsError(
            details="Session already closed or invalid")

    await db.commit()
    return f"Logged out from session {user_data.session_id}"


async def refresh_user_token(
    refresh_data: RefreshSchema,
    jwt_manager: JWTAuthManagerInterface,
) -> RefreshSchema:
    """
    Crud function for refresh user access token by refresh token
    Parameters:
        refresh_data (RefreshSchema): refresh token
    Returns:
        RefreshSchema: new access token
    """
    decoded_data = jwt_manager.decode_refresh_token(refresh_data.token)

    new_access_token = jwt_manager.create_access_token(data={
        "user_id": decoded_data["user_id"],
        "email": decoded_data["email"],
        "is_active": decoded_data["is_active"],
        "session_id": decoded_data["session_id"],
    })

    return RefreshSchema(
        token=new_access_token,
    )