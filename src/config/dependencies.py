from typing import Annotated

from fastapi import Depends

from src.config.settings import Settings
from src.security.interfaces import JWTAuthManagerInterface
from src.security.token_manager import JWTAuthManager


def get_settings() -> Settings:
    """
    Retrieve the application settings based on the current environment.
    """
    return Settings()


def get_jwt_manager(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JWTAuthManagerInterface:
    """
    Create and return a JWT authentication manager instance.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )
