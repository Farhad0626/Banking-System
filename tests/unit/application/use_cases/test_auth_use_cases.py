from datetime import UTC, datetime
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from banking.application.context.session_context import Session
from banking.application.dto.auth.change_password_dto import ChangePasswordRequest
from banking.application.dto.auth.login_dto import LoginRequest
from banking.application.dto.auth.register_dto import RegisterCustomerRequest
from banking.application.use_cases.auth.change_password import ChangePassword
from banking.application.use_cases.auth.login import Login
from banking.application.use_cases.auth.logout import Logout
from banking.domain.exceptions.auth_exceptions import (
    AccountLockedException,
    InvalidCredentialsException,
)
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException
from banking.domain.value_objects.customer_id import CustomerId


def session(customer_id: int = 19) -> Session:
    return Session(customer_id, "CUSTOMER", datetime.now(UTC))


def test_login_success_returns_result_and_authenticated_session_and_resets_limiter() -> None:
    customer = SimpleNamespace(
        id=CustomerId(19),
        username="ada",
        password_hash="hash",
        is_deleted=False,
        ensure_can_login=Mock(),
    )
    customers = Mock()
    customers.get_by_username.return_value = customer
    hasher = Mock()
    hasher.verify.return_value = True
    limiter = Mock()
    limiter.is_locked.return_value = False

    result, session = Login(customers, hasher, limiter).execute(LoginRequest("ada", "Secret123"))

    assert result.customer_id == 19
    assert result.role == "CUSTOMER"
    assert session.customer_id == 19
    assert session.role == "CUSTOMER"
    assert session.authenticated_at.tzinfo is UTC
    limiter.reset.assert_called_once_with("ada")
    limiter.register_failure.assert_not_called()


def test_login_rejects_locked_user_without_repository_lookup() -> None:
    customers = Mock()
    limiter = Mock()
    limiter.is_locked.return_value = True

    with pytest.raises(AccountLockedException):
        Login(customers, Mock(), limiter).execute(LoginRequest("ada", "Secret123"))

    customers.get_by_username.assert_not_called()
    limiter.register_failure.assert_not_called()


@pytest.mark.parametrize("deleted", [False, True])
def test_login_registers_failure_for_unknown_or_deleted_customer(deleted: bool) -> None:
    customers = Mock()
    customers.get_by_username.return_value = SimpleNamespace(is_deleted=True) if deleted else None
    limiter = Mock()
    limiter.is_locked.return_value = False

    with pytest.raises(InvalidCredentialsException):
        Login(customers, Mock(), limiter).execute(LoginRequest("ada", "Secret123"))

    limiter.register_failure.assert_called_once_with("ada")
    limiter.reset.assert_not_called()


def test_login_registers_failure_for_wrong_password() -> None:
    customer = SimpleNamespace(
        id=CustomerId(19),
        is_deleted=False,
        password_hash="hash",
        ensure_can_login=Mock(),
    )
    customers = Mock()
    customers.get_by_username.return_value = customer
    hasher = Mock()
    hasher.verify.return_value = False
    limiter = Mock()
    limiter.is_locked.return_value = False

    with pytest.raises(InvalidCredentialsException):
        Login(customers, hasher, limiter).execute(LoginRequest("ada", "wrong"))

    customer.ensure_can_login.assert_called_once_with()
    limiter.register_failure.assert_called_once_with("ada")
    limiter.reset.assert_not_called()


def test_login_propagates_ineligible_customer_failure_without_reset() -> None:
    customer = SimpleNamespace(
        id=CustomerId(19),
        is_deleted=False,
        password_hash="hash",
        ensure_can_login=Mock(side_effect=ValueError),
    )
    customers = Mock()
    customers.get_by_username.return_value = customer
    limiter = Mock()
    limiter.is_locked.return_value = False

    with pytest.raises(ValueError):
        Login(customers, Mock(), limiter).execute(LoginRequest("ada", "Secret123"))

    limiter.register_failure.assert_not_called()
    limiter.reset.assert_not_called()


def test_change_password_verifies_hashes_new_password_and_saves_customer() -> None:
    customer = SimpleNamespace(password_hash="old-hash", username="ada", change_password=Mock())
    customers = Mock()
    customers.get_by_id.return_value = customer
    hasher = Mock()
    hasher.verify.return_value = True
    hasher.hash.return_value = "new-hash"

    ChangePassword(customers, hasher).execute(
        ChangePasswordRequest(19, "Oldpass123", "Newpass123"),
        session(),
    )

    hasher.verify.assert_called_once_with("Oldpass123", "old-hash")
    hasher.hash.assert_called_once_with("Newpass123")
    customer.change_password.assert_called_once_with("new-hash")
    customers.update.assert_called_once_with(customer)


def test_change_password_rejects_unknown_customer_or_wrong_old_password() -> None:
    customers = Mock()
    customers.get_by_id.return_value = None
    hasher = Mock()
    use_case = ChangePassword(customers, hasher)

    with pytest.raises(CustomerNotFoundException):
        use_case.execute(ChangePasswordRequest(19, "Oldpass123", "Newpass123"), session())
    hasher.verify.assert_not_called()

    customer = SimpleNamespace(password_hash="hash")
    customers.get_by_id.return_value = customer
    hasher.verify.return_value = False
    with pytest.raises(InvalidCredentialsException):
        use_case.execute(ChangePasswordRequest(19, "wrong", "Newpass123"), session())
    hasher.hash.assert_not_called()
    customers.update.assert_not_called()


@pytest.mark.parametrize(
    ("new_password", "strict"),
    [("short", False), ("NoSpecial123", True), ("Secret123", False)],
)
def test_change_password_rejects_invalid_or_username_password(
    new_password: str, strict: bool
) -> None:
    customer = SimpleNamespace(password_hash="hash", username="Secret123", change_password=Mock())
    customers = Mock()
    customers.get_by_id.return_value = customer
    hasher = Mock()
    hasher.verify.return_value = True

    with pytest.raises(ValueError):
        ChangePassword(customers, hasher, password_strict_mode=strict).execute(
            ChangePasswordRequest(19, "Oldpass123", new_password),
            session(),
        )

    hasher.hash.assert_not_called()
    customers.update.assert_not_called()


def test_logout_is_a_safe_no_op() -> None:
    assert Logout().execute() is None


def test_register_customer_saves_hashed_customer_and_returns_result() -> None:
    register_module = import_module("banking.application.use_cases.auth.register_customer")
    request = RegisterCustomerRequest(
        first_name="Ada",
        last_name="Lovelace",
        national_id="1111111111",
        mobile="09123456789",
        email="ada@example.test",
        username="ada",
        password="Secret123",
    )
    customers = Mock()
    customers.get_by_national_id.return_value = None
    customers.get_by_mobile.return_value = None
    customers.get_by_username.return_value = None
    customers.add.return_value = SimpleNamespace(id=CustomerId(19), username="ada")
    hasher = Mock()
    hasher.hash.return_value = "stored-hash"

    result = register_module.RegisterCustomer(customers, hasher).execute(request)

    assert result.customer_id == 19
    assert result.username == "ada"
    hasher.hash.assert_called_once_with("Secret123")
    customers.add.assert_called_once()
    customer = customers.add.call_args.args[0]
    assert customer.id is None
    assert customer.mobile.value == "09123456789"
    assert customer.email == "ada@example.test"
    assert customer.password_hash == "stored-hash"
    assert customer.is_active
    assert not customer.is_restricted


def test_login_and_change_password_paths_import_from_public_modules() -> None:
    assert import_module("banking.application.use_cases.auth.login").Login is Login
    assert (
        import_module("banking.application.use_cases.auth.change_password").ChangePassword
        is ChangePassword
    )
