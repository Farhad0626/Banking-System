from decimal import Decimal

from banking.domain.entities.account import Account
from banking.domain.value_objects.money import Money


class InterestCalculator:
    """Service for calculating interest on bank accounts."""

    @staticmethod
    def calculate_interest(account: Account) -> Money:
        """Calculate the interest for a given account based on its balance and interest rate."""
        if account.terms.interest_rate is None:
            return Money.zero()

        interest_amount = account.balance.amount * account.terms.interest_rate
        return Money(interest_amount.quantize(Decimal("0.01")))
