from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from banking.domain.entities.account import Account, AccountTerms
from banking.domain.entities.customer import Customer
from banking.domain.entities.transaction import Transaction
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.enums.transaction_status import TransactionStatus
from banking.domain.enums.transaction_type import TransactionType
from banking.domain.exceptions.customer_exceptions import DuplicateNationalIdException
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.phone_number import PhoneNumber


def make_customer(
    *,
    national_id: str = "1111111111",
    mobile: str = "09123456789",
    username: str = "integration-user",
) -> Customer:
    return Customer(
        id=None,
        first_name="Integration",
        last_name="Customer",
        national_id=NationalId(national_id),
        mobile=PhoneNumber(mobile),
        email="integration@example.test",
        username=username,
        password_hash="test-hash",
        is_active=True,
        is_restricted=False,
    )


def add_customer(repositories, **kwargs) -> Customer:
    return repositories["customers"].add(make_customer(**kwargs))


def make_account(customer_id: CustomerId, account_number: str, balance: str = "20.00") -> Account:
    return Account(
        id=None,
        account_number=AccountNumber(account_number),
        customer_id=customer_id,
        account_type=AccountType.CHECKING,
        account_status=AccountStatus.ACTIVE,
        balance=Money(Decimal(balance)),
        terms=AccountTerms(overdraft_limit=Decimal("100.00")),
    )


def test_customer_repository_persists_round_trip_search_and_soft_delete(repositories) -> None:
    customer = add_customer(repositories)

    assert customer.id is not None
    loaded = repositories["customers"].get_by_id(customer.id.value)
    assert loaded is not None
    assert loaded.national_id == NationalId("1111111111")
    assert loaded.mobile == PhoneNumber("09123456789")
    assert loaded.email == "integration@example.test"
    assert loaded.created_at is not None

    assert repositories["customers"].get_by_username("integration-user").id == customer.id
    assert [item.id for item in repositories["customers"].search("Integrat")] == [customer.id]

    repositories["customers"].delete(customer.id.value)
    assert repositories["customers"].get_by_id(customer.id.value) is None
    assert repositories["customers"].search("integration-user") == []


def test_customer_repository_maps_database_unique_violation(repositories) -> None:
    add_customer(repositories)

    with pytest.raises(DuplicateNationalIdException):
        repositories["customers"].add(
            make_customer(
                national_id="1111111111",
                mobile="09120000001",
                username="another-integration-user",
            )
        )


def test_account_repository_persists_accounts_and_filters_search(repositories) -> None:
    customer = add_customer(repositories)
    account = repositories["accounts"].add(
        make_account(customer.id, "1234567890123456", balance="35.50")
    )
    assert account.id is not None

    loaded = repositories["accounts"].get_by_id(account.id)
    assert loaded is not None
    assert loaded.account_number == AccountNumber("1234567890123456")
    assert loaded.balance == Money(Decimal("35.50"))
    assert loaded.account_status is AccountStatus.ACTIVE
    assert loaded.customer_id == customer.id
    assert (
        repositories["accounts"].get_by_account_number(account.account_number.value).id
        == account.id
    )
    assert [item.id for item in repositories["accounts"].get_by_customer_id(customer.id.value)] == [
        account.id
    ]
    assert account.id in [item.id for item in repositories["accounts"].search("CHECKING", "ACTIVE")]

    locked = repositories["accounts"].get_by_id(account.id, for_update=True)
    assert locked is not None
    assert locked.id == account.id


def test_transaction_repository_persists_and_searches_ledger(repositories) -> None:
    customer = add_customer(repositories)
    account = repositories["accounts"].add(make_account(customer.id, "2234567890123456"))
    transaction = Transaction(
        id=None,
        transaction_type=TransactionType.DEPOSIT,
        amount=Money(Decimal("12.75")),
        destination_account_id=account.id,
    )
    transaction.mark_completed()
    saved = repositories["transactions"].add(transaction)

    loaded = repositories["transactions"].get_by_id(saved.id)
    assert loaded is not None
    assert loaded.transaction_type is TransactionType.DEPOSIT
    assert loaded.amount == Money(Decimal("12.75"))
    assert loaded.status is TransactionStatus.COMPLETED
    assert [item.id for item in repositories["transactions"].get_by_account_id(account.id)] == [
        saved.id
    ]

    now = datetime.now(UTC)
    results = repositories["transactions"].search(
        account_id=account.id,
        transaction_type="DEPOSIT",
        date_from=now - timedelta(days=1),
        date_to=now + timedelta(days=1),
    )
    assert [item.id for item in results] == [saved.id]
