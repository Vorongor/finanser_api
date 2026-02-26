from fastapi import APIRouter

from .user_router import user_router
from ..config import get_settings

settings = get_settings()

api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_v1_router.include_router(user_router)


@api_v1_router.get("/")
def index():
    return {"Hello": "World"}