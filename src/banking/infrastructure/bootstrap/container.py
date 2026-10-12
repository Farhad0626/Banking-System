from dataclasses import dataclass

from banking.application.ports.configuration.configuration_service import ConfigurationService
from banking.application.ports.generators.account_number_generator import AccountNumberGenerator
from banking.application.ports.notifications.notification_sender import NotificationSender
from banking.application.ports.persistence.unit_of_work import UnitOfWork
from banking.application.ports.repositories.account_repository import AccountRepository
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.application.ports.repositories.transaction_repository import TransactionRepository
from banking.application.ports.security.password_hasher import PasswordHasher
from banking.application.ports.security.rate_limiter import RateLimiter


@dataclass
class Container:
    """Holds all constructed dependencies, typed as ports so use cases never see concrete classes."""

    config: ConfigurationService
    customers: CustomerRepository
    accounts: AccountRepository
    transactions: TransactionRepository
    unit_of_work: UnitOfWork
    password_hasher: PasswordHasher
    rate_limiter: RateLimiter
    account_number_generator: AccountNumberGenerator
    notification_sender: NotificationSender
