from fastapi import APIRouter

user_router = APIRouter()

@user_router.get("/", tags=["Auth"])
async def root():
    return {"message": "You are authenticated"}