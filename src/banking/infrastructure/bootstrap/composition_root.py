from banking.application.context.application_context import ApplicationContext
from banking.application.ports.configuration.configuration_service import ConfigurationService
from banking.application.use_cases.account.activate_account import ActivateAccount
from banking.application.use_cases.account.apply_interest import ApplyInterest
from banking.application.use_cases.account.create_account import CreateAccount
from banking.application.use_cases.account.deactivate_account import DeactivateAccount
from banking.application.use_cases.account.get_account import GetAccount
from banking.application.use_cases.account.get_balance import GetBalance
from banking.application.use_cases.account.list_my_accounts import ListMyAccounts
from banking.application.use_cases.account.lookup_account_by_number import LookupAccountByNumber
from banking.application.use_cases.auth.change_password import ChangePassword
from banking.application.use_cases.auth.login import Login
from banking.application.use_cases.auth.logout import Logout
from banking.application.use_cases.auth.register_customer import RegisterCustomer
from banking.application.use_cases.customer.activate_customer import ActivateCustomer
from banking.application.use_cases.customer.delete_customer import DeleteCustomer
from banking.application.use_cases.customer.get_customer import GetCustomer
from banking.application.use_cases.customer.restrict_customer import RestrictCustomer
from banking.application.use_cases.customer.search_customers import SearchCustomers
from banking.application.use_cases.transaction.deposit import Deposit
from banking.application.use_cases.transaction.get_transaction_history import GetTransactionHistory
from banking.application.use_cases.transaction.search_transactions import SearchTransactions
from banking.application.use_cases.transaction.transfer_funds import TransferFunds
from banking.application.use_cases.transaction.withdrawl import Withdrawl
from banking.domain.services.interest_calculator import InterestCalculator
from banking.domain.services.transfer_service import TransferService
from banking.infrastructure.bootstrap.container import Container
from banking.infrastructure.database.connection import ConnectionFactory, PerCallConnectionProvider
from banking.infrastructure.database.postgres_unit_of_work import PostgresUnitOfWork
from banking.infrastructure.generators.account_number_generator import RandomAccountNumberGenerator
from banking.infrastructure.notifications.console_notification import ConsoleNotificationSender
from banking.infrastructure.repositories.postgres_account_repository import (
    PostgresAccountRepository,
)
from banking.infrastructure.repositories.postgres_customer_repository import (
    PostgresCustomerRepository,
)
from banking.infrastructure.repositories.postgres_transaction_repository import (
    PostgresTransactionRepository,
)
from banking.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from banking.infrastructure.security.in_memory_rate_limiter import InMemoryRateLimiter


def build_container(config: ConfigurationService) -> Container:
    """Create the concrete infrastructure implementations and place them in a Container."""
    factory = ConnectionFactory.from_configuration(config)
    provider = PerCallConnectionProvider(factory)

    return Container(
        config=config,
        customers=PostgresCustomerRepository(provider),
        accounts=PostgresAccountRepository(provider),
        transactions=PostgresTransactionRepository(provider),
        unit_of_work=PostgresUnitOfWork(factory),
        password_hasher=BcryptPasswordHasher(rounds=config.get_int("BCRYPT_ROUNDS", 12)),
        rate_limiter=InMemoryRateLimiter(
            max_attempts=config.get_int("LOGIN_MAX_FAILED_ATTEMPTS", 5),
            window_seconds=config.get_int("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 60),
            lock_seconds=config.get_int("LOGIN_LOCK_DURATION_SECONDS", 60),
        ),
        account_number_generator=RandomAccountNumberGenerator(),
        notification_sender=ConsoleNotificationSender(),
    )


def build_use_cases(container: Container) -> dict[str, object]:
    """Instantiate every use case with its dependencies and register it under a name."""
    strict = container.config.get_bool("PASSWORD_STRICT_MODE", False)
    interest_calculator = InterestCalculator()
    transfer_service = TransferService()

    return {
        # Auth
        "register_customer": RegisterCustomer(
            container.customers, container.password_hasher, strict
        ),
        "login": Login(container.customers, container.password_hasher, container.rate_limiter),
        "logout": Logout(),
        "change_password": ChangePassword(container.customers, container.password_hasher, strict),
        # Customer
        "get_customer": GetCustomer(container.customers),
        "search_customers": SearchCustomers(container.customers),
        "activate_customer": ActivateCustomer(container.customers),
        "restrict_customer": RestrictCustomer(container.customers),
        "delete_customer": DeleteCustomer(container.unit_of_work),
        # Account
        "create_account": CreateAccount(
            container.customers,
            container.accounts,
            container.account_number_generator,
            container.config,
        ),
        "get_account": GetAccount(container.accounts),
        "get_balance": GetBalance(container.accounts),
        "activate_account": ActivateAccount(container.accounts),
        "deactivate_account": DeactivateAccount(container.accounts),
        "apply_interest": ApplyInterest(container.accounts, interest_calculator),
        "list_my_accounts": ListMyAccounts(container.accounts),
        "lookup_account_by_number": LookupAccountByNumber(container.accounts),
        # Transaction
        "deposit": Deposit(container.unit_of_work),
        "withdraw": Withdrawl(container.unit_of_work),
        "transfer_funds": TransferFunds(container.unit_of_work, transfer_service),
        "get_transaction_history": GetTransactionHistory(
            container.transactions, container.accounts
        ),
        "search_transactions": SearchTransactions(container.transactions, container.accounts),
    }


def compose(config: ConfigurationService) -> ApplicationContext:
    """Wire everything together and return the ApplicationContext used by the presentation layer."""
    container = build_container(config)
    return ApplicationContext(use_cases=build_use_cases(container))
