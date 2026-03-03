from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    create_profile,
    retrieve_profile,
    update_profile,
    delete_profile,
)
from src.database import get_db
from src.exceptions import (
    ProfileAlreadyExists,
    ProfileNotFound,
    ProfileOperationError,
    TokenExpiredError,
    InvalidTokenError,
    UserEmailNotConfirmed,
    LoggedOutError,
)
from src.schemas import (
    AuthUserSchema,
    ProfileCreateSchema,
    ProfileReadSchema,
    ProfileUpdateSchema,
)
from src.security.utils import get_current_user

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


@profile_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfileReadSchema,
    summary="Create profile for current user",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Email not confirmed"},
        409: {"description": "Profile already exists"},
        500: {"description": "Profile operation error"},
    },
)
async def create(
    profile_data: ProfileCreateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> ProfileReadSchema:
    """
    Create a profile for the authenticated user.

    - **email** and **user_id** are taken from the authenticated session.
    - All profile fields are taken from the request body.
    - Only one profile is allowed per user.
    """
    try:
        return await create_profile(
            profile_data=profile_data,
            db=db,
            auth_user=auth_user,
        )
    except (TokenExpiredError, InvalidTokenError, LoggedOutError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)
        )
    except UserEmailNotConfirmed as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(err)
        )
    except ProfileAlreadyExists as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(err)
        )
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        )


@profile_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ProfileReadSchema,
    summary="Get current user's profile",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Email not confirmed"},
        404: {"description": "Profile not found"},
    },
)
async def retrieve(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> ProfileReadSchema:
    """
    Retrieve the profile for the authenticated user.
    """
    try:
        return await retrieve_profile(db=db, auth_user=auth_user)
    except (TokenExpiredError, InvalidTokenError, LoggedOutError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)
        )
    except UserEmailNotConfirmed as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(err)
        )
    except ProfileNotFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        )


@profile_router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ProfileReadSchema,
    summary="Partially update current user's profile",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Email not confirmed"},
        404: {"description": "Profile not found"},
        500: {"description": "Profile operation error"},
    },
)
async def update(
    profile_data: ProfileUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> ProfileReadSchema:
    """
    Partially update the profile for the authenticated user.

    Only fields provided in the request body will be updated.
    """
    try:
        return await update_profile(
            update_data=profile_data,
            db=db,
            auth_user=auth_user,
        )
    except (TokenExpiredError, InvalidTokenError, LoggedOutError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)
        )
    except UserEmailNotConfirmed as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(err)
        )
    except ProfileNotFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        )
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        )


@profile_router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user's profile",
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Email not confirmed"},
        404: {"description": "Profile not found"},
        500: {"description": "Profile operation error"},
    },
)
async def delete(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> None:
    """
    Delete the profile for the authenticated user.
    """
    try:
        await delete_profile(db=db, auth_user=auth_user)
    except (TokenExpiredError, InvalidTokenError, LoggedOutError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)
        )
    except UserEmailNotConfirmed as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(err)
        )
    except ProfileNotFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(err)
        )
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err),
        )
