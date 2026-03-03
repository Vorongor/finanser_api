from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import ProfileConnectionModel, ProfileModel
from src.enums import ProfileConnectionStatus
from src.exceptions import (
    PermissionDenied,
    ProfileNotFound,
    ProfileOperationError,
)
from src.schemas import (
    AuthUserSchema,
    MyConnectionSchema,
    ProfileReadSchema,
    SocialConnectionSchema,
    SocialConnectionsResponseSchema,
    SocialResponseSchema,
    SocialSearchSchema,
)


async def _get_profile_for_user(
    auth_user: AuthUserSchema,
    db: AsyncSession,
) -> ProfileModel:
    stmt = await db.execute(
        select(ProfileModel).where(ProfileModel.user_id == auth_user.id)
    )
    profile = stmt.scalar_one_or_none()
    if not profile:
        raise ProfileNotFound() from None
    return profile


async def search_users(
    search_params: SocialSearchSchema,
    db: AsyncSession,
    auth_user: AuthUserSchema,
) -> SocialResponseSchema:
    """
    Search for other user profiles.

    - If unique_key is provided, returns at most one profile with that key.
    - Otherwise, filters by optional first_name, last_name, job_title.
    - The current user's own profile is excluded from the result.
    """
    base_query = select(ProfileModel)

    if search_params.unique_key:
        base_query = base_query.where(
            ProfileModel.unique_key == search_params.unique_key
        )
    else:
        filters = []
        if search_params.first_name:
            filters.append(
                ProfileModel.first_name.ilike(f"%{search_params.first_name}%")
            )
        if search_params.last_name:
            filters.append(
                ProfileModel.last_name.ilike(f"%{search_params.last_name}%")
            )
        if search_params.job_title:
            filters.append(
                ProfileModel.job_title.ilike(f"%{search_params.job_title}%")
            )
        if filters:
            base_query = base_query.where(and_(*filters))

    base_query = base_query.where(ProfileModel.user_id != auth_user.id)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = base_query.offset(search_params.skip).limit(search_params.limit)
    result = await db.execute(stmt)
    profiles = result.scalars().all()

    items = [ProfileReadSchema.model_validate(profile) for profile in profiles]
    return SocialResponseSchema(
        items=items,
        total=total,
        skip=search_params.skip,
        limit=search_params.limit,
    )


async def get_connections(
    db: AsyncSession,
    auth_user: AuthUserSchema,
    filter_data: MyConnectionSchema,
) -> SocialConnectionsResponseSchema:
    """
    Retrieve list of connections for the authenticated user.
    Optionally filtered by connection status.
    Connections blocked by other users are hidden; blocked connections are
    visible only if blocked_by is the authenticated user.
    """

    profile = await _get_profile_for_user(auth_user=auth_user, db=db)

    base_query = (
        select(ProfileConnectionModel)
        .options(
            joinedload(ProfileConnectionModel.requester_profile),
            joinedload(ProfileConnectionModel.target_profile),
        )
        .where(
            or_(
                ProfileConnectionModel.requester_profile_id == profile.id,
                ProfileConnectionModel.target_profile_id == profile.id,
            )
        )
    )

    if filter_data.status:
        base_query = base_query.where(
            ProfileConnectionModel.status == filter_data.status
        )

    base_query = base_query.where(
        or_(
            ProfileConnectionModel.status != ProfileConnectionStatus.BLOCKED,
            ProfileConnectionModel.blocked_by == auth_user.id,
        )
    )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = base_query.offset(filter_data.skip).limit(filter_data.limit)
    result = await db.execute(stmt)
    connections = result.scalars().all()

    items = [
        SocialConnectionSchema(
            id=conn.id,
            status=conn.status,
            requester_profile=ProfileReadSchema.model_validate(
                conn.requester_profile
            ),
            target_profile=ProfileReadSchema.model_validate(
                conn.target_profile
            ),
        )
        for conn in connections
    ]

    return SocialConnectionsResponseSchema(
        items=items,
        total=total,
        skip=filter_data.skip,
        limit=filter_data.limit,
    )


async def send_connection(
    target_profile_id: int,
    db: AsyncSession,
    auth_user: AuthUserSchema,
) -> SocialConnectionSchema:
    """
    Create a connection between the authenticated user and another profile
    with initial status Pending.
    """
    requester_profile = await _get_profile_for_user(auth_user=auth_user, db=db)

    if requester_profile.id == target_profile_id:
        raise ProfileOperationError("Cannot create connection to own profile")

    target_profile = await db.get(ProfileModel, target_profile_id)
    if not target_profile:
        raise ProfileNotFound() from None

    existing_stmt = await db.execute(
        select(ProfileConnectionModel).where(
            or_(
                and_(
                    ProfileConnectionModel.requester_profile_id
                    == requester_profile.id,
                    ProfileConnectionModel.target_profile_id
                    == target_profile.id,
                ),
                and_(
                    ProfileConnectionModel.requester_profile_id
                    == target_profile.id,
                    ProfileConnectionModel.target_profile_id
                    == requester_profile.id,
                ),
            )
        )
    )
    existing_connection = existing_stmt.scalar_one_or_none()
    if existing_connection:
        raise ProfileOperationError(
            "Connection between these profiles already exists"
        )

    connection = ProfileConnectionModel(
        requester_profile_id=requester_profile.id,
        target_profile_id=target_profile.id,
        status=ProfileConnectionStatus.PENDING,
    )
    db.add(connection)
    try:
        await db.commit()
        await db.refresh(connection)
    except IntegrityError as err:
        raise ProfileOperationError(
            details="Error occurred while trying to create connection"
        ) from err

    await db.refresh(
        connection, attribute_names=["requester_profile", "target_profile"]
    )

    return SocialConnectionSchema(
        id=connection.id,
        status=connection.status,
        requester_profile=ProfileReadSchema.model_validate(
            connection.requester_profile
        ),
        target_profile=ProfileReadSchema.model_validate(
            connection.target_profile
        ),
    )


async def accept_connection(
    connection_id: int,
    db: AsyncSession,
    auth_user: AuthUserSchema,
) -> SocialConnectionSchema:
    """
    Accept a connection invitation by setting its status to CONNECTED.
    Only the target profile's owner can accept the connection.
    """
    stmt = await db.execute(
        select(ProfileConnectionModel)
        .options(
            joinedload(ProfileConnectionModel.requester_profile),
            joinedload(ProfileConnectionModel.target_profile),
        )
        .where(ProfileConnectionModel.id == connection_id)
    )
    connection = stmt.scalar_one_or_none()
    if not connection:
        raise ProfileOperationError("Connection not found") from None

    target_profile = connection.target_profile
    if target_profile.user_id != auth_user.id:
        raise PermissionDenied()

    connection.status = ProfileConnectionStatus.CONNECTED
    try:
        await db.commit()
        await db.refresh(connection)
    except IntegrityError as err:
        raise ProfileOperationError(
            details="Error occurred while trying to accept connection"
        ) from err

    return SocialConnectionSchema(
        id=connection.id,
        status=connection.status,
        requester_profile=ProfileReadSchema.model_validate(
            connection.requester_profile
        ),
        target_profile=ProfileReadSchema.model_validate(
            connection.target_profile
        ),
    )


async def block_connection(
    connection_id: int,
    db: AsyncSession,
    auth_user: AuthUserSchema,
) -> SocialConnectionSchema:
    """
    Block a connection by setting its status to BLOCKED.
    Either side of the connection may block it.
    The user who blocked the connection is stored in blocked_by.
    """
    stmt = await db.execute(
        select(ProfileConnectionModel)
        .options(
            joinedload(ProfileConnectionModel.requester_profile),
            joinedload(ProfileConnectionModel.target_profile),
        )
        .where(ProfileConnectionModel.id == connection_id)
    )
    connection = stmt.scalar_one_or_none()
    if not connection:
        raise ProfileOperationError("Connection not found") from None

    requester_profile = connection.requester_profile
    target_profile = connection.target_profile

    if auth_user.id not in (requester_profile.user_id, target_profile.user_id):
        raise PermissionDenied()

    connection.status = ProfileConnectionStatus.BLOCKED
    connection.blocked_by = auth_user.id
    try:
        await db.commit()
        await db.refresh(connection)
    except IntegrityError as err:
        raise ProfileOperationError(
            details="Error occurred while trying to block connection"
        ) from err

    return SocialConnectionSchema(
        id=connection.id,
        status=connection.status,
        requester_profile=ProfileReadSchema.model_validate(
            connection.requester_profile
        ),
        target_profile=ProfileReadSchema.model_validate(
            connection.target_profile
        ),
    )


async def unblock_connection(
    connection_id: int,
    db: AsyncSession,
    auth_user: AuthUserSchema,
) -> SocialConnectionSchema:
    """
    Unblock a connection if it was blocked by the authenticated user.
    After unblocking, the connection becomes CONNECTED.
    """
    stmt = await db.execute(
        select(ProfileConnectionModel)
        .options(
            joinedload(ProfileConnectionModel.requester_profile),
            joinedload(ProfileConnectionModel.target_profile),
        )
        .where(ProfileConnectionModel.id == connection_id)
    )
    connection = stmt.scalar_one_or_none()
    if not connection:
        raise ProfileOperationError("Connection not found") from None

    if (
        connection.status != ProfileConnectionStatus.BLOCKED
        or connection.blocked_by != auth_user.id
    ):
        raise PermissionDenied(
            details="You are not allowed to unblock connection"
        )

    connection.status = ProfileConnectionStatus.PENDING
    connection.blocked_by = None

    try:
        await db.commit()
        await db.refresh(connection)
    except IntegrityError as err:
        raise ProfileOperationError(
            details="Error occurred while trying to unblock connection"
        ) from err

    return SocialConnectionSchema(
        id=connection.id,
        status=connection.status,
        requester_profile=ProfileReadSchema.model_validate(
            connection.requester_profile
        ),
        target_profile=ProfileReadSchema.model_validate(
            connection.target_profile
        ),
    )


async def remove_connection(
    connection_id: int,
    db: AsyncSession,
    auth_user: AuthUserSchema,
) -> None:
    """
    Remove a connection.
    Authenticated user must be a participant and cannot remove a connection
    that was blocked by the other user.
    """
    stmt = await db.execute(
        select(ProfileConnectionModel)
        .options(
            joinedload(ProfileConnectionModel.requester_profile),
            joinedload(ProfileConnectionModel.target_profile),
        )
        .where(ProfileConnectionModel.id == connection_id)
    )
    connection = stmt.scalar_one_or_none()
    if not connection:
        raise ProfileOperationError("Connection not found")

    requester_profile = connection.requester_profile
    target_profile = connection.target_profile

    if auth_user.id not in (requester_profile.user_id, target_profile.user_id):
        raise PermissionDenied()

    if (
        connection.status == ProfileConnectionStatus.BLOCKED
        and connection.blocked_by is not None
        and connection.blocked_by != auth_user.id
    ):
        raise PermissionDenied()

    try:
        await db.delete(connection)
        await db.commit()
    except IntegrityError as err:
        raise ProfileOperationError(
            details="Error occurred while trying to remove connection"
        ) from err
