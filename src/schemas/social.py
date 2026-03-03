from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.orm import Mapped

from src.enums import ProfileConnectionStatus
from src.schemas.profile import ProfileReadSchema


class SocialSearchSchema(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=25, ge=1)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    unique_key: Optional[UUID] = None


class MyConnectionSchema(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=25, ge=1)
    status: Optional[ProfileConnectionStatus] = "",


class SocialResponseSchema(BaseModel):
    items: List[ProfileReadSchema]
    total: int
    skip: int
    limit: int


class SocialConnectionSchema(BaseModel):
    id: int
    status: ProfileConnectionStatus
    requester_profile: ProfileReadSchema
    target_profile: ProfileReadSchema


class SocialConnectionsResponseSchema(BaseModel):
    items: List[SocialConnectionSchema]
    total: int
    skip: int
    limit: int

