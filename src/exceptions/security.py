class BaseSecurityException(Exception):
    """
    Base security exception, that raise during security operation
    """

    def __init__(self, details: str | None = None) -> None:
        if details is None:
            details = "Something went wrong during security operation"
        super().__init__(details)


class PasswordError(BaseSecurityException):
    """
    Raised when password is wrong or weak
    """
    details = "Password is wrong or weak"


class TokenExpiredError(BaseSecurityException):
    """Raised when token is expired"""
    details = "Your token has expired"


class InvalidTokenError(BaseSecurityException):
    """Raised when token is invalid"""
    details = "Your token is invalid"


class IncorrectCredentialsError(BaseSecurityException):
    """Raised when credentials are incorrect"""
    details = "Incorrect credentials"


class UserEmailNotConfirmed(BaseSecurityException):
    """Raised when user email is not confirmed"""
    details = "User email is not confirmed. Please confirm your email"


class PermissionDenied(BaseSecurityException):
    """Raised when user has no permission"""
    details = "User has no permission for action"


class LoggedOutError(BaseSecurityException):
    """Raised when user logged out and try to get access token"""
    details = "User logged out and try to get data"

