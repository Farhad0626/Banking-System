import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from banking.application.dto.transaction.transaction_dto import (
    DepositRequest,
    TransferRequest,
    WithdrawalRequest,
)
from banking.application.use_cases.transaction.deposit import Deposit
from banking.application.use_cases.transaction.transfer_funds import TransferFunds
from banking.application.use_cases.transaction.withdrawl import Withdrawl
from banking.domain.entities.account import Account, AccountTerms
from banking.domain.entities.customer import Customer
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.services.transfer_service import TransferService
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.money import Money
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.phone_number import PhoneNumber
from banking.infrastructure.database.connection import PerCallConnectionProvider
from banking.infrastructure.database.postgres_unit_of_work import PostgresUnitOfWork
from banking.infrastructure.repositories.postgres_account_repository import (
    PostgresAccountRepository,
)
from banking.infrastructure.repositories.postgres_customer_repository import (
    PostgresCustomerRepository,
)
from banking.infrastructure.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)


def make_customer(suffix: str) -> Customer:
    first_nine = f"{int(suffix[:8], 16) % 10**9:09d}"
    weighted_sum = sum(int(digit) * (10 - index) for index, digit in enumerate(first_nine))
    remainder = weighted_sum % 11
    check_digit = remainder if remainder < 2 else 11 - remainder
    national_id = f"{first_nine}{check_digit}"
    mobile_tail = f"{int(suffix[8:14], 16) % 10**7:07d}"
    return Customer(
        id=None,
        first_name="Money",
        last_name="Movement",
        national_id=NationalId(national_id),
        mobile=PhoneNumber(f"0912{mobile_tail}"),
        email=f"{suffix}@example.test",
        username=f"movement-{suffix}",
        password_hash="test-hash",
        is_active=True,
        is_restricted=False,
    )


def make_account(customer_id: CustomerId, account_number: str) -> Account:
    return Account(
        id=None,
        account_number=AccountNumber(account_number),
        customer_id=customer_id,
        account_type=AccountType.CHECKING,
        account_status=AccountStatus.ACTIVE,
        balance=Money(Decimal("100.00")),
        terms=AccountTerms(overdraft_limit=Decimal("50.00")),
    )


def test_deposit_withdrawal_and_transfer_persist_balances_and_ledger(postgres_factory) -> None:
    suffix = uuid.uuid4().hex
    customer = make_customer(suffix)
    provider = PerCallConnectionProvider(postgres_factory)
    customers = PostgresCustomerRepository(provider)
    accounts = PostgresAccountRepository(provider)
    transactions = PostgresTransactionRepository(provider)
    customer_id = None
    account_ids: list[int] = []

    try:
        saved_customer = customers.add(customer)
        assert saved_customer.id is not None
        customer_id = saved_customer.id.value
        account_number_a = f"{int(suffix[:15], 16) % (9 * 10**15) + 10**15:016d}"
        account_number_b = f"{int(suffix[15:30], 16) % (9 * 10**15) + 10**15:016d}"
        account_a = accounts.add(make_account(CustomerId(customer_id), account_number_a))
        account_b = accounts.add(make_account(CustomerId(customer_id), account_number_b))
        assert account_a.id is not None and account_b.id is not None
        account_ids.extend([account_a.id, account_b.id])

        session = SimpleNamespace(
            customer_id=customer_id,
            role="CUSTOMER",
            authenticated_at=datetime.now(UTC),
            is_owner=lambda owner_id: owner_id == customer_id,
        )
        unit_of_work = PostgresUnitOfWork(postgres_factory)

        deposited = Deposit(unit_of_work).execute(
            DepositRequest(account_a.id, "25.00"),
            session,
        )
        withdrawn = Withdrawl(unit_of_work).execute(
            WithdrawalRequest(account_a.id, "10.00"),
            session,
        )
        transferred = TransferFunds(unit_of_work, TransferService()).execute(
            TransferRequest(account_a.id, account_b.id, "20.00"),
            session,
        )

        assert deposited.amount == "25.00"
        assert withdrawn.amount == "10.00"
        assert transferred.amount == "20.00"
        assert accounts.get_by_id(account_a.id).balance == Money(Decimal("95.00"))
        assert accounts.get_by_id(account_b.id).balance == Money(Decimal("120.00"))
        assert len(transactions.get_by_account_id(account_a.id)) == 3
        assert len(transactions.get_by_account_id(account_b.id)) == 1
    finally:
        cleanup = postgres_factory.create()
        try:
            if account_ids:
                cleanup.execute(
                    "DELETE FROM transactions WHERE source_account_id = ANY(%s) "
                    "OR destination_account_id = ANY(%s)",
                    (account_ids, account_ids),
                )
                cleanup.execute("DELETE FROM accounts WHERE id = ANY(%s)", (account_ids,))
            if customer_id is not None:
                cleanup.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
            cleanup.commit()
        finally:
            cleanup.close()
