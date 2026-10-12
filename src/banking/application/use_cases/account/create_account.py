from decimal import Decimal, InvalidOperation

from banking.application.context.session_context import Session
from banking.application.dto.account.account_dto import AccountView, CreateAccountRequest
from banking.application.ports.configuration.configuration_service import ConfigurationService
from banking.application.ports.generators.account_number_generator import AccountNumberGenerator
from banking.application.ports.repositories.account_repository import AccountRepository
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.domain.entities.account import Account, AccountTerms
from banking.domain.enums.account_status import AccountStatus
from banking.domain.enums.account_type import AccountType
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException
from banking.domain.exceptions.customer_exceptions import CustomerNotFoundException
from banking.domain.value_objects.account_number import AccountNumber
from banking.domain.value_objects.money import Money


class CreateAccount:
    """Creates a new account for the specified customer."""

    def __init__(
        self,
        customer_repository: CustomerRepository,
        account_repository: AccountRepository,
        account_number_generator: AccountNumberGenerator,
        configuration: ConfigurationService,
    ) -> None:
        self._customers = customer_repository
        self._accounts = account_repository
        self._number_generator = account_number_generator
        self._config = configuration

    def _build_terms(self, account_type: AccountType) -> AccountTerms:
        if account_type == AccountType.SAVINGS:
            return AccountTerms(interest_rate=self._config.get_decimal("SAVINGS_INTEREST_RATE"))
        if account_type == AccountType.TERM_DEPOSIT:
            return AccountTerms(
                interest_rate=self._config.get_decimal("TERM_DEPOSIT_INTEREST_RATE")
            )
        if account_type == AccountType.CHECKING:
            return AccountTerms(
                overdraft_limit=self._config.get_decimal("CHECKING_WITHDRAWAL_LIMIT")
            )
        return AccountTerms()

    def _generate_unique_account_number(self, max_attempts: int = 5) -> AccountNumber:
        for _ in range(max_attempts):
            candidate = AccountNumber(self._number_generator.generate())
            if self._accounts.get_by_account_number(candidate.value) is None:
                return candidate
        raise RuntimeError(
            "The generation of a unique account number followed several unsuccessful attempts."
        )

    def execute(self, request: CreateAccountRequest, session: Session) -> AccountView:
        if not session.is_owner(request.customer_id):
            raise AuthenticationFailedException("Access to this user account is not permitted.")
        customer = self._customers.get_by_id(request.customer_id)
        if customer is None or customer.is_deleted:
            raise CustomerNotFoundException(f"Customer with ID {request.customer_id} not found.")
        if customer.id is None:
            raise RuntimeError("Customer repository returned a customer without an ID.")

        try:
            initial_balance = Money(Decimal(request.initial_deposit))
            if initial_balance.is_negative():
                raise ValueError("The opening balance cannot be negative.")
        except InvalidOperation:
            raise ValueError("The initial deposit amount is invalid.")

        account_type = AccountType(request.account_type)
        terms = self._build_terms(account_type)
        account_number = self._generate_unique_account_number()

        account = Account(
            id=0,
            account_number=account_number,
            customer_id=customer.id,
            account_type=account_type,
            account_status=AccountStatus.ACTIVE,
            balance=initial_balance,
            terms=terms,
        )
        saved = self._accounts.add(account)
        if saved.id is None:
            raise RuntimeError("Account repository did not assign an ID.")

        return AccountView(
            account_id=saved.id,
            account_number=saved.account_number.value,
            customer_id=saved.customer_id.value,
            account_type=saved.account_type.value,
            balance=str(saved.balance),
            status=saved.account_status.value,
        )
