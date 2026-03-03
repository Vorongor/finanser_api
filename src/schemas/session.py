from pydantic import BaseModel, field_validator

from src.exceptions import PasswordError
from src.validators import validate_password


class LoginRequestSchema(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v) -> str:
        try:
            return validate_password(v)
        except ValueError as err:
            raise PasswordError(str(err))


class LoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LogoutResponseSchema(BaseModel):
    message: str


class RefreshSchema(BaseModel):
    token: str


class AuthUserSchema(BaseModel):
    id: int
    email: str
    is_active: bool
    session_id: str
