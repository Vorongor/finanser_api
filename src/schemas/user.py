from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

from src.validators import validate_password
from src.exceptions import PasswordError


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value) -> str:
        return str(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        try:
            return validate_password(value)
        except ValueError as error:
            raise PasswordError(details=str(error))


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class UserUpdateSchema(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return str(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        try:
            return validate_password(value)
        except ValueError as error:
            raise PasswordError(details=str(error))
