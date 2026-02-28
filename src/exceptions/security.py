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