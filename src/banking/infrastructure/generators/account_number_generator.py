import secrets

from banking.application.ports.generators.account_number_generator import AccountNumberGenerator


class RandomAccountNumberGenerator(AccountNumberGenerator):
    """Generates unpredictable 16-digit account numbers; final uniqueness is enforced by the database."""

    def generate(self) -> str:
        """Return a random 16-digit number that never starts with zero."""
        return str(secrets.randbelow(9 * 10**15) + 10**15)
