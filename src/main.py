from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse

from .api import api_v1_router
from .exceptions import PasswordError

app = FastAPI()

app.include_router(api_v1_router)


@app.exception_handler(PasswordError)
async def password_error(
        request: Request,  # noqa
        exc: PasswordError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=str(exc)
    )
