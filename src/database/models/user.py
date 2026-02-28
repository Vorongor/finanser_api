from datetime import datetime

from sqlalchemy import Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column

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
