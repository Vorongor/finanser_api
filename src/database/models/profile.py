import uuid
from datetime import date, datetime

from sqlalchemy import (
    UUID,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.enums import CurrencyType, ProfileConnectionStatus
from src.schemas import ProfileBaseSchema


class ProfileConnectionModel(Base):
    __tablename__ = "profile_connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ProfileConnectionStatus] = mapped_column(
        Enum(ProfileConnectionStatus),
        nullable=False,
    )
    blocked_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    requester_profile: Mapped["ProfileModel"] = relationship(
        "ProfileModel",
        foreign_keys=[requester_profile_id],
        back_populates="sent_connections",
    )
    target_profile: Mapped["ProfileModel"] = relationship(
        "ProfileModel",
        foreign_keys=[target_profile_id],
        back_populates="received_connections",
    )


class ProfileModel(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    birt_date: Mapped[date] = mapped_column(Date, nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    salary: Mapped[int] = mapped_column(Integer, nullable=False)
    default_currency: Mapped[CurrencyType] = mapped_column(
        Enum(CurrencyType),
        nullable=False,
    )
    unique_key: Mapped[uuid.UUID] = mapped_column(
        UUID,
        unique=True,
        nullable=False,
    )
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
    )

    sent_connections: Mapped[list["ProfileConnectionModel"]] = relationship(
        "ProfileConnectionModel",
        foreign_keys=[ProfileConnectionModel.requester_profile_id],
        back_populates="requester_profile",
        cascade="all, delete-orphan",
    )
    received_connections: Mapped[list["ProfileConnectionModel"]] = relationship(
        "ProfileConnectionModel",
        foreign_keys=[ProfileConnectionModel.target_profile_id],
        back_populates="target_profile",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def create(
        cls,
        email: str,
        user_id: int,
        profile_data: ProfileBaseSchema,
    ) -> "ProfileModel":
        """
        Fabric method to create a new profile for authenticated user
        """
        unique_key = uuid.uuid4()
        profile = ProfileModel(
            email=email,
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            birt_date=profile_data.birt_date,
            job_title=profile_data.job_title,
            salary=profile_data.salary,
            default_currency=profile_data.default_currency,
            unique_key=unique_key,
            bio=profile_data.bio or None,
            user_id=user_id,
        )
        return profile
