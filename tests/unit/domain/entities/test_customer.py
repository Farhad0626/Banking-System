from datetime import UTC, datetime

import pytest

from banking.domain.entities.customer import Customer
from banking.domain.exceptions.customer_exceptions import (
    CustomerInactiveException,
    CustomerRestrictedException,
)
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.phone_number import PhoneNumber


def make_customer(
    *,
    active: bool = True,
    restricted: bool = False,
    deleted_at: datetime | None = None,
) -> Customer:
    return Customer(
        id=CustomerId(1),
        first_name="First",
        last_name="Last",
        national_id=NationalId("1111111111"),
        mobile=PhoneNumber("09123456789"),
        email="user@example.com",
        username="customer",
        password_hash="hashed",
        is_active=active,
        is_restricted=restricted,
        deleted_at=deleted_at,
    )


def test_customer_defaults_and_deleted_property() -> None:
    customer = make_customer()

    assert not customer.is_deleted
    assert customer.created_at <= customer.updated_at
    assert customer.id == CustomerId(1)

    deleted = make_customer(deleted_at=datetime(2026, 1, 1, tzinfo=UTC))
    assert deleted.is_deleted


def test_active_unrestricted_customer_can_log_in() -> None:
    make_customer().ensure_can_login()


def test_inactive_customer_cannot_log_in() -> None:
    customer = make_customer(active=False, restricted=True)

    with pytest.raises(CustomerInactiveException, match="customer is inactive"):
        customer.ensure_can_login()


def test_restricted_active_customer_cannot_log_in() -> None:
    with pytest.raises(CustomerRestrictedException, match="customer is restricted"):
        make_customer(restricted=True).ensure_can_login()


def test_customer_transition_methods_update_entity_state() -> None:
    customer = make_customer(active=False)

    customer.activate()
    assert customer.is_active
    assert customer.updated_at >= customer.created_at

    customer.restrict()
    assert customer.is_restricted

    customer.change_password("new-hash")
    assert customer.password_hash == "new-hash"

    customer.mark_deleted()
    assert customer.is_deleted
    assert not customer.is_active
