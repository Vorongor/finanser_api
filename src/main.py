from fastapi import FastAPI

from .api import api_v1_router

app = FastAPI()

app.include_router(api_v1_router)

@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}