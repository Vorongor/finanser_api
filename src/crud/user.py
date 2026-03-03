from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.database.models import UserModel, ActivationTokenModel
from src.exceptions import (
    BaseUserException,
    UserAlreadyExists,
    UserNotFound,
    PermissionDenied,
)
from src.schemas import (
    UserReadSchema,
    UserCreateSchema,
    UserUpdateSchema,
    AuthUserSchema,
)
from src.security.interfaces import JWTAuthManagerInterface
from src.tasks import send_activation_email_task


async def retrieve_user_by_email(
        email: str,
        db: AsyncSession,
) -> UserModel | None:
    """
    Helper function for retrieving a user by email.
    Parameters:
        email: str email of user to retrieve
        db: database session
    Returns:
        UserModel | None: retrieved user if it exists
    """
    smtp = await db.execute(select(UserModel).where(UserModel.email == email))
    user = smtp.scalar_one_or_none()
    return user


async def _retrieve_user_by_id(
        user_id: int,
        db: AsyncSession,
) -> UserModel | None:
    """
    Retrieves a user by ID.
    Args:
        user_id: Primary key of the user.
        db: Async database session.
    Returns:
        UserModel: The retrieved user object.
    Raises:
        UserNotFound: If no user exists with the given ID.
    """
    user = await db.get(
        UserModel,
        user_id,
        options=[
            joinedload(UserModel.activation_token),
            joinedload(UserModel.password_reset_token),
            joinedload(UserModel.refresh_tokens),
        ]
    )
    if not user:
        raise UserNotFound()
    return user


async def create_new_user(
        user_data: UserCreateSchema,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
) -> UserReadSchema:
    """
    Crud operation for creating new user
    Parameters:
        user_data: UserCreateSchema
        db: database session
    Returns:
        UserReadSchema: new user
    """
    try:
        existing_user = await retrieve_user_by_email(user_data.email, db)
        if existing_user:
            raise UserAlreadyExists()
        new_user = UserModel.create(
            email=user_data.email,
            raw_password=user_data.password,
        )
        db.add(new_user)
        await db.flush()
        token = jwt_manager.create_activation_token()
        activation_token = ActivationTokenModel(
            token=token,
            user_id=new_user.id,
        )
        db.add(activation_token)
        await db.commit()
        await db.refresh(new_user)
        await send_activation_email_task.kiq(
            email=new_user.email,
            activation_link=(
                f"http://127.0.0.1:8000/api/v1/users/activate?token={token}"
            ))
        return UserReadSchema(
            id=new_user.id,
            email=new_user.email,
        )
    except IntegrityError:
        raise UserAlreadyExists()


async def get_list_of_all_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
) -> list[UserReadSchema]:
    """
    Crud operation for getting all users according to permission
    Parameters:
        db: database session
    Returns:
        list[UserReadSchema]: list of all users
    """
    # TODO Add permission check
    smtp = await db.execute(
        select(UserModel)
        .order_by(UserModel.email)
        .offset(skip)
        .limit(limit)
    )
    result = smtp.scalars().all()
    return [
        UserReadSchema(id=user.id, email=user.email)
        for user in result
    ]


async def partial_update_user(
        user_id: int,
        update_data: UserUpdateSchema,
        db: AsyncSession,
        auth_user: AuthUserSchema
) -> UserReadSchema:
    """
    Crud operation for partial update of user
    Parameters:
        user_id: pk of user to update
        update_data: UserUpdateSchema
        db: database session
        auth_user: authenticated user
    Returns:
        UserReadSchema: updated user
    """
    if user_id != auth_user.id:
        raise PermissionDenied()
    user = await _retrieve_user_by_id(user_id, db)
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(user, key, value)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return UserReadSchema(id=user.id, email=user.email)
    except IntegrityError:
        raise UserAlreadyExists()


async def delete_user(
        user_id: int,
        db: AsyncSession,
        auth_user: AuthUserSchema
) -> None:
    """
    Crud operation for deleting user
    Parameters:
        user_id: pk of user to delete
        db: database session
        auth_user: authenticated user
    """
    if user_id != auth_user.id:
        raise PermissionDenied()
    user = await _retrieve_user_by_id(user_id, db)
    try:
        await db.delete(user)
        await db.commit()
    except IntegrityError:
        raise BaseUserException()


async def activate_user(
        activation_token: str,
        db: AsyncSession,
) -> str:
    """
    Crud operation for activating user by token
    Parameters:
        activation_token: token of user to activate
    Returns:
        str: message about the activation user
    """
    try:
        smtp = await db.execute(
            select(ActivationTokenModel)
            .options(selectinload(ActivationTokenModel.user))
            .where(ActivationTokenModel.token == activation_token)
        )
        db_token = smtp.scalar_one_or_none()
        if not db_token:
            raise UserNotFound()
        user = db_token.user
        if not user:
            raise UserNotFound()
        if user.is_active:
            await db.delete(db_token)
            await db.commit()
            return "User is already activated"
        user.is_active = True
        db.add(user)
        await db.delete(db_token)
        await db.commit()
        return "User successfully activated"
    except IntegrityError:
        raise BaseUserException(
            details="Error occurred while trying to activate user",
        )
