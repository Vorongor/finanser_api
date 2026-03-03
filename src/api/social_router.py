from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    accept_connection,
    block_connection,
    get_connections,
    remove_connection,
    search_users,
    send_connection,
    unblock_connection,
)
from src.database import get_db
from src.exceptions import (
    PermissionDenied,
    ProfileNotFound,
    ProfileOperationError,
)
from src.schemas import (
    AuthUserSchema,
    MyConnectionSchema,
    SocialConnectionSchema,
    SocialConnectionsResponseSchema,
    SocialResponseSchema,
    SocialSearchSchema,
)
from src.security.utils import get_current_user

social_router = APIRouter(prefix="/social", tags=["Social"])


@social_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=SocialResponseSchema,
)
async def get_social_list(
    social_search: Annotated[SocialSearchSchema, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> SocialResponseSchema:
    result = await search_users(
        auth_user=auth_user,
        db=db,
        search_params=social_search,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Users not found",
        ) from None

    return result


@social_router.get(
    "/my-connection",
    status_code=status.HTTP_200_OK,
    response_model=SocialConnectionsResponseSchema,
)
async def get_my_connections(
    filter_data: Annotated[MyConnectionSchema, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> SocialConnectionsResponseSchema:
    result = await get_connections(
        filter_data=filter_data,
        db=db,
        auth_user=auth_user,
    )
    return result


@social_router.get(
    "/{target_id}/invite",
    status_code=status.HTTP_201_CREATED,
    response_model=SocialConnectionSchema,
)
async def connect_users(
    target_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> SocialConnectionSchema:
    try:
        result = await send_connection(
            target_profile_id=target_id, db=db, auth_user=auth_user
        )
        return result
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except ProfileNotFound as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@social_router.get(
    "/{connection_id}/accept",
    status_code=status.HTTP_200_OK,
    response_model=SocialConnectionSchema,
)
async def accept(
    connection_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> SocialConnectionSchema:
    try:
        result = await accept_connection(
            connection_id=connection_id,
            db=db,
            auth_user=auth_user,
        )
        return result
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except PermissionDenied as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err


@social_router.get(
    "/{connection_id}/block",
    status_code=status.HTTP_200_OK,
    response_model=SocialConnectionSchema,
)
async def block(
    connection_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> SocialConnectionSchema:
    try:
        result = await block_connection(
            connection_id=connection_id,
            db=db,
            auth_user=auth_user,
        )
        return result
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except PermissionDenied as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err


@social_router.get(
    "/{connection_id}/unblock",
    status_code=status.HTTP_200_OK,
    response_model=SocialConnectionSchema,
)
async def unblock(
    connection_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> SocialConnectionSchema:
    try:
        result = await unblock_connection(
            connection_id=connection_id,
            db=db,
            auth_user=auth_user,
        )
        return result
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except PermissionDenied as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err


@social_router.delete(
    "/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    connection_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[AuthUserSchema, Depends(get_current_user)],
) -> JSONResponse:
    try:
        await remove_connection(
            connection_id=connection_id,
            db=db,
            auth_user=auth_user,
        )
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
    except ProfileOperationError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        ) from err
    except PermissionDenied as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
