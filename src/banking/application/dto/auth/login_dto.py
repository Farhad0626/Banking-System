from dataclasses import dataclass


@dataclass
class LoginRequest:
    """Data transfer object for login requests."""

    username: str
    password: str


@dataclass
class LoginResult:
    """Data transfer object for the result of a login attempt."""

    customer_id: int
    role: str
