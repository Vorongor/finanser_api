from fastapi import APIRouter

from .user_router import user_router
from .session_router import session_router
from .profile_router import profile_router
from src.config import get_settings

settings = get_settings()

api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_v1_router.include_router(user_router)
api_v1_router.include_router(session_router)
api_v1_router.include_router(profile_router)
