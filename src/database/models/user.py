from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    func,
    Boolean,
    UniqueConstraint,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base
from src.security import hash_password, verify_password


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    _hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    activation_token: Mapped[Optional["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    password_reset_token: Mapped[
        Optional["PasswordResetTokenModel"]] = relationship(
        "PasswordResetTokenModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @classmethod
    def create(cls, email: str, raw_password: str) -> "UserModel":
        """
        Factory method to create a new user
        Parameters:
            email: Email address of the user
            raw_password: Password of the user
        Returns:
            UserModel: New user instance
        """

        user = cls(email=email)
        user.password = raw_password
        return user

    @property
    def password(self) -> None:
        """
        User password can`t be retrieved only set
        """
        raise AttributeError(
            "Password is write-only. Use the setter to set the password."
        )

    @password.setter
    def password(self, password: str) -> None:
        """
        Setter method for User password
        Parameters:
            password: raw password of the user
        """
        hashed_password = hash_password(password)

        self._hashed_password = hashed_password

    def check_password(self, password: str) -> bool:
        """
        Function to check if the password matches the hashed password
        Parameters:
            password: raw password of the user
        Returns:
            bool: True if the password matches the hashed password
        """
        return verify_password(password, self._hashed_password)


class TokenBaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=True)
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1)
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class ActivationTokenModel(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="activation_token"
    )

    __table_args__ = (UniqueConstraint("user_id"),)


class PasswordResetTokenModel(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="password_reset_token"
    )

    __table_args__ = (UniqueConstraint("user_id"),)


class RefreshTokenModel(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="refresh_tokens"
    )
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
    )

    @classmethod
    def create(
            cls, user_id: int | Mapped[int], days_valid: int, token: str
    ) -> "RefreshTokenModel":
        """
        Factory method to create a new RefreshTokenModel instance.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
        return cls(user_id=user_id, expires_at=expires_at, token=token)
