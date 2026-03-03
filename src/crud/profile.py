from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ProfileModel
from src.exceptions import (
    ProfileAlreadyExists,
    ProfileNotFound,
    ProfileOperationError,
)
from src.schemas import (
    AuthUserSchema,
    ProfileCreateSchema,
    ProfileReadSchema,
    ProfileUpdateSchema,
)


async def _retrieve_profile_by_user_id(
        user_id: int,
        db: AsyncSession,
) -> ProfileModel | None:
    """
    Helper function for retrieving a profile by user id.
    Parameters:
        user_id: int id of user to retrieve profile for
        db: database session
    Returns:
        ProfileModel | None: retrieved profile if it exists
    """
    stmt = await db.execute(
        select(ProfileModel).where(ProfileModel.user_id == user_id)
    )
    profile = stmt.scalar_one_or_none()
    return profile


async def create_profile(
        profile_data: ProfileCreateSchema,
        db: AsyncSession,
        auth_user: AuthUserSchema,
) -> ProfileReadSchema:
    """
    Crud operation for creating a new profile for authenticated user.
    Parameters:
        profile_data: ProfileCreateSchema
        db: database session
        auth_user: authenticated user
    Returns:
        ProfileReadSchema: created profile
    """
    existing_profile = await _retrieve_profile_by_user_id(
        user_id=auth_user.id,
        db=db,
    )
    if existing_profile:
        raise ProfileAlreadyExists()

    profile = ProfileModel.create(
        email=auth_user.email,
        user_id=auth_user.id,
        profile_data=profile_data,
    )
    db.add(profile)
    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        raise ProfileOperationError(
            details="Error occurred while trying to create profile"
        )

    return ProfileReadSchema.model_validate(profile)


async def retrieve_profile(
        db: AsyncSession,
        auth_user: AuthUserSchema,
) -> ProfileReadSchema:
    """
    Crud operation for retrieving profile of authenticated user if it exists.
    Parameters:
        db: database session
        auth_user: authenticated user
    Returns:
        ProfileReadSchema: retrieved profile
    """
    profile = await _retrieve_profile_by_user_id(
        user_id=auth_user.id,
        db=db,
    )
    if not profile:
        raise ProfileNotFound()

    return ProfileReadSchema.model_validate(profile)


async def update_profile(
        update_data: ProfileUpdateSchema,
        db: AsyncSession,
        auth_user: AuthUserSchema,
) -> ProfileReadSchema:
    """
    Crud operation for partial update of profile for authenticated user.
    Parameters:
        update_data: ProfileUpdateSchema
        db: database session
        auth_user: authenticated user
    Returns:
        ProfileReadSchema: updated profile
    """
    profile = await _retrieve_profile_by_user_id(
        user_id=auth_user.id,
        db=db,
    )
    if not profile:
        raise ProfileNotFound()

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)

    db.add(profile)
    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        raise ProfileOperationError(
            details="Error occurred while trying to update profile")

    return ProfileReadSchema.model_validate(profile)


async def delete_profile(
        db: AsyncSession,
        auth_user: AuthUserSchema,
) -> None:
    """
    Crud operation for deleting profile of authenticated user.
    Parameters:
        db: database session
        auth_user: authenticated user
    """
    profile = await _retrieve_profile_by_user_id(
        user_id=auth_user.id,
        db=db,
    )
    if not profile:
        raise ProfileNotFound()

    try:
        await db.delete(profile)
        await db.commit()
    except IntegrityError:
        raise ProfileOperationError(
            details="Error occurred while trying to delete profile")
