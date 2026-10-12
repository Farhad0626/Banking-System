import bcrypt

from banking.application.ports.security.password_hasher import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """Hashes and verifies passwords with bcrypt, using a fresh random salt for every hash."""

    def __init__(self, rounds: int = 12) -> None:
        """Set the bcrypt work factor (lower values are only for fast tests)."""
        self._rounds = rounds

    def hash(self, plain_password: str) -> str:
        """Return the bcrypt hash of a plain-text password."""
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if the plain password matches the hash; malformed hashes simply return False."""
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False
