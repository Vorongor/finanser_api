from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.enums import CurrencyType


class ProfileBaseSchema(BaseModel):
    first_name: str
    last_name: str
    birt_date: date
    job_title: str
    salary: int
    default_currency: CurrencyType
    bio: Optional[str] = ""


class ProfileCreateSchema(ProfileBaseSchema):
    pass


class ProfileUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birt_date: Optional[date] = None
    job_title: Optional[str] = None
    salary: Optional[int] = None
    default_currency: Optional[CurrencyType] = None
    bio: Optional[str] = None


class ProfileReadSchema(ProfileBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime
    updated_at: datetime
