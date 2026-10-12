import uuid

from banking.domain.entities.customer import Customer
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.phone_number import PhoneNumber
from banking.infrastructure.database.connection import PerCallConnectionProvider
from banking.infrastructure.database.postgres_unit_of_work import PostgresUnitOfWork
from banking.infrastructure.repositories.postgres_customer_repository import (
    PostgresCustomerRepository,
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
        first_name="Unit",
        last_name="OfWork",
        national_id=NationalId(national_id),
        mobile=PhoneNumber(f"0912{mobile_tail}"),
        email=f"{suffix}@example.test",
        username=f"uow-{suffix}",
        password_hash="test-hash",
        is_active=True,
        is_restricted=False,
    )


def test_unit_of_work_commits_and_rolls_back_real_database_changes(postgres_factory) -> None:
    suffix = uuid.uuid4().hex
    customer = make_customer(suffix)
    rollback_customer = make_customer(uuid.uuid4().hex)
    uow = PostgresUnitOfWork(postgres_factory)

    try:
        with uow as active:
            active.customers.add(customer)
            active.commit()

        try:
            with uow as active:
                active.customers.add(rollback_customer)
                raise RuntimeError("force rollback")
        except RuntimeError as exc:
            assert str(exc) == "force rollback"

        customers = PostgresCustomerRepository(PerCallConnectionProvider(postgres_factory))
        stored = customers.get_by_username(customer.username)
        assert stored is not None
        assert stored.id == customer.id
        assert customers.get_by_username(rollback_customer.username) is None
    finally:
        cleanup = postgres_factory.create()
        try:
            cleanup.execute(
                "DELETE FROM customers WHERE username IN (%s, %s)",
                (customer.username, rollback_customer.username),
            )
            cleanup.commit()
        finally:
            cleanup.close()
