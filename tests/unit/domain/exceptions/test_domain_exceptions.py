import pytest

from banking.domain.exceptions.account_exceptions import (
    AccountInactiveException,
    AccountNotFoundException,
    InvalidAccountOperationException,
)
from banking.domain.exceptions.auth_exceptions import (
    AccountLockedException,
    AuthenticationFailedException,
    InvalidCredentialsException,
)
from banking.domain.exceptions.customer_exceptions import (
    CustomerInactiveException,
    CustomerNotFoundException,
    CustomerRestrictedException,
    DuplicateMobileException,
    DuplicateNationalIdException,
    DuplicateUsernameException,
)
from banking.domain.exceptions.domain_exception import DomainException
from banking.domain.exceptions.insufficient_balance import InsufficientBalanceException
from banking.domain.exceptions.invalid_account_state import InvalidAccountStateException
from banking.domain.exceptions.invalid_transaction import InvalidTransactionException
from banking.domain.exceptions.transaction_exceptions import (
    InvalidAmountException,
    SameAccountTransferException,
    TransactionFailedException,
)


@pytest.mark.parametrize(
    ("exception_type", "parent_type"),
    [
        (DomainException, Exception),
        (AccountNotFoundException, DomainException),
        (AccountInactiveException, InvalidAccountStateException),
        (InvalidAccountOperationException, InvalidAccountStateException),
        (InvalidAccountStateException, DomainException),
        (InsufficientBalanceException, DomainException),
        (InvalidTransactionException, DomainException),
        (InvalidAmountException, InvalidTransactionException),
        (SameAccountTransferException, InvalidTransactionException),
        (TransactionFailedException, InvalidTransactionException),
        (InvalidCredentialsException, DomainException),
        (AuthenticationFailedException, DomainException),
        (AccountLockedException, DomainException),
        (CustomerNotFoundException, DomainException),
        (DuplicateNationalIdException, DomainException),
        (DuplicateMobileException, DomainException),
        (DuplicateUsernameException, DomainException),
        (CustomerInactiveException, DomainException),
        (CustomerRestrictedException, DomainException),
    ],
)
def test_domain_exception_hierarchy_and_message(
    exception_type: type[Exception], parent_type: type[Exception]
) -> None:
    error = exception_type("domain error")

    assert isinstance(error, parent_type)
    assert str(error) == "domain error"
    assert error.args == ("domain error",)
