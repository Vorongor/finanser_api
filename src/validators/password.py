import re


def validate_password(password: str) -> str:
    """
    Helper function to validate a password strength before creating the user.
    Parameters
        password: String to validate, raw password
    Returns:
        str: Same password, if it pas all checks
    """
    if len(password) < 6:
        raise ValueError("Password must contain at least 6 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lower letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[@$!%*?&#]", password):
        raise ValueError(
            "Password must contain at least one special "
            "character: @, $, !, %, *, ?, #, &."
        )
    return password
