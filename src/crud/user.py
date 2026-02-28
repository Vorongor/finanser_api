from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.database.models import UserModel
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
    user = await db.get(UserModel, user_id)
    if not user:
        raise UserNotFound()
    return user


async def create_new_user(
        user_data: UserCreateSchema,
        db: AsyncSession,
) -> UserReadSchema:
    """
    Crud operation for creating new user
    Parameters:
        user_data: UserCreateSchema
        db: database session
    Returns:
        UserReadSchema: new user
    """
    existing_user = await retrieve_user_by_email(user_data.email, db)
    if existing_user:
        raise UserAlreadyExists()
    new_user = UserModel.create(
        email=user_data.email,
        raw_password=user_data.password,
    )
    db.add(new_user)
    # TODO Activate email abd trigger budget and profile creation
    try:
        await db.commit()
        await db.refresh(new_user)
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
    Crud operation for for getting all users according to permission
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
