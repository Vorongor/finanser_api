from typing import Annotated

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    create_new_user,
    get_list_of_all_users,
    partial_update_user,
    delete_user,
)
from src.database import get_db
from src.exceptions import (
    BaseUserException,
    BaseSecurityException,
    UserNotFound,
    UserAlreadyExists
)
from src.schemas import (
    UserCreateSchema,
    UserReadSchema,
    UserUpdateSchema
)


user_router = APIRouter(prefix="/users", tags=["Users operations"])


@user_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserReadSchema,
    summary="Register a new user",
    responses={
        400: {"description": "User already exists or validation error"},
        422: {"description": "Validation Error"},
    },
)
async def register(
        user_data: UserCreateSchema,
        db: Annotated[AsyncSession, Depends(get_db)]
) -> UserReadSchema:
    """
    Endpoint to register a new user

    Parameters:
        - user_data (UserCreateSchema): user data to register:
            - **email**: Must be unique
            - **password**: Should be strong (minimum 6 characters,
            1 uppercase letter, 1 digit, 1 special character)

    Returns:
        - **UserReadSchema**: user data after successful registration
    """
    try:
        new_user = await create_new_user(user_data=user_data, db=db)
        return new_user
    except UserAlreadyExists as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )


@user_router.get(
    "/",
    response_model=list[UserReadSchema],
    status_code=status.HTTP_200_OK,
    summary="Get list of all users",
    responses={
        403: {"description": "Permission denied"},
        400: {"description": "Bad Request"},
    },
)
async def get_users(
        db: Annotated[AsyncSession, Depends(get_db)],
        skip: int = 0,
        limit: int = 100,
) -> list[UserReadSchema]:
    """
    Endpoint to retrieve a paginated list of users.
    Parameters:
        - **skip**: Number of records to skip
        - **limit**: Maximum number of records to return
    """
    try:
        users = await get_list_of_all_users(db=db, skip=skip, limit=limit)
        return users
    except BaseSecurityException as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err)
        )
    except BaseUserException as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )


@user_router.patch(
    "/{user_id}",
    response_model=UserReadSchema,
    status_code=status.HTTP_200_OK, summary="Partially update a user",
    responses={
        404: {"description": "User not found"},
        400: {"description": "Update conflict or validation error"},
    },
)
async def update(
        user_id: int,
        user_data: UserUpdateSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> UserReadSchema:
    """
    Update user fields selectively.
    Parameters:
        - **user_id**: The unique ID of the user
        - **user_data**: Fields to update (email, password.)
    Returns:
        - **UserReadSchema**: partially updated user data
    """
    try:
        user = await partial_update_user(
            user_id=user_id, user_data=user_data, db=db
        )
        return user
    except BaseUserException as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )


@user_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        404: {"description": "User not found"},
        400: {"description": "Deletion failed"},
    },
)
async def delete(
        user_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Remove a user record permanently from the system.
    """
    try:
        await delete_user(user_id=user_id, db=db)
    except UserNotFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )
    except BaseUserException as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
