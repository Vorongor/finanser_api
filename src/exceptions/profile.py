class BaseProfileException(Exception):
    """
    Base profile exception, that raise during operation around the profile
    """

    def __init__(self, details: str | None = None) -> None:
        if details is None:
            details = "Something went wrong during profile operation"
        super().__init__(details)


class ProfileAlreadyExists(BaseProfileException):
    details = "Profile for this user already exists"


class ProfileNotFound(BaseProfileException):
    details = "Profile for this user does not exist"


class ProfileOperationError(BaseProfileException):
    details = "Error occurred during profile operation"

