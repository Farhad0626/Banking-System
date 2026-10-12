from enum import Enum


class UserRole(str, Enum):
    """Enum representing the role of a user in the banking system."""

    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
