from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.exceptions.account_exceptions import (
    AccountInactiveException,
    InsufficientBalanceException,
)
from banking.domain.exceptions.transaction_exceptions import InvalidAmountException
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money


@dataclass
class AccountTerms:
    """Value object representing the terms of an account."""

    interest_rate: Decimal | None = None
    overdraft_limit: Decimal | None = None
    term_start_date: date | None = None
    term_end_date: date | None = None


@dataclass
class Account:
    """Entity representing a bank account."""

    id: int | None
    account_number: AccountNumber
    customer_id: CustomerId
    account_type: AccountType
    account_status: AccountStatus
    balance: Money
    terms: AccountTerms = field(default_factory=AccountTerms)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        """Check if the account is deleted."""
        return self.deleted_at is not None

    def ensure_active(self) -> None:
        """Ensure that the account is active."""
        if self.account_status != AccountStatus.ACTIVE:
            raise AccountInactiveException(f"Account {self.account_number.value} is not active.")

    def deposit(self, amount: Money) -> None:
        """Deposit money into the account."""
        self.ensure_active()
        if not amount.is_positive():
            raise InvalidAmountException("Deposit amount must be positive.")
        self.balance += amount
        self.updated_at = datetime.now(UTC)

    def withdraw(self, amount: Money) -> None:
        """Withdraw money from the account."""
        self.ensure_active()
        if not amount.is_positive():
            raise InvalidAmountException("Withdrawal amount must be positive.")

        available_balance = self.balance
        if self.account_type == AccountType.CHECKING and self.terms.overdraft_limit:
            available_balance = Money(self.balance.amount + self.terms.overdraft_limit)

        if amount > available_balance:
            raise InsufficientBalanceException(
                f"Insufficient funds for withdrawal from account {self.account_number.value}."
            )

        self.balance -= amount
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Activate the account."""
        self.account_status = AccountStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Deactivate the account."""
        self.account_status = AccountStatus.INACTIVE
        self.updated_at = datetime.now(UTC)

    def mark_deleted(self) -> None:
        """Mark the account as deleted."""
        self.deleted_at = datetime.now(UTC)
        self.account_status = AccountStatus.DELETED
        self.updated_at = datetime.now(UTC)
