from fastapi import APIRouter

from src.config import get_settings

from .profile_router import profile_router
from .session_router import session_router
from .social_router import social_router
from .user_router import user_router

settings = get_settings()

api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_v1_router.include_router(user_router)
api_v1_router.include_router(session_router)
api_v1_router.include_router(profile_router)
api_v1_router.include_router(social_router)


@api_v1_router.get("/health", tags=["helthcheck"], status_code=200)
def health_check():
    return {"status": "ok"}
