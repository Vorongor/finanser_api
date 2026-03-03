class BaseUserException(Exception):
    """
    Base user exception, that raise during operation around the users
    """

    def __init__(self, details: str | None = None) -> None:
        if details is None:
            details = "Something went wrong during user operation"
        super().__init__(details)


class UserAlreadyExists(BaseUserException):
    details = "User with provided email already exists"


class UserNotFound(BaseUserException):
    details = "User with provided id does not exist"
