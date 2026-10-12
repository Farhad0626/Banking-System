from decimal import Decimal

from banking.domain.entities.account import Account, AccountTerms
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.services.interest_calculator import InterestCalculator
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money


def make_account(balance: str, interest_rate: Decimal | None) -> Account:
    return Account(
        id=1,
        account_number=AccountNumber("1234567890123456"),
        customer_id=CustomerId(1),
        account_type=AccountType.SAVINGS,
        account_status=AccountStatus.ACTIVE,
        balance=Money.of(balance),
        terms=AccountTerms(interest_rate=interest_rate),
    )


def test_interest_is_zero_when_no_rate_is_configured() -> None:
    assert InterestCalculator.calculate_interest(make_account("100", None)) == Money.zero()


def test_interest_is_balance_times_rate_quantized_to_cents() -> None:
    account = make_account("250.00", Decimal("0.05"))

    assert InterestCalculator.calculate_interest(account) == Money.of("12.50")


def test_interest_can_be_negative_for_negative_balance_or_rate() -> None:
    assert InterestCalculator.calculate_interest(make_account("-100", Decimal("0.05"))) == Money.of(
        "-5.00"
    )
    assert InterestCalculator.calculate_interest(make_account("100", Decimal("-0.05"))) == Money.of(
        "-5.00"
    )
