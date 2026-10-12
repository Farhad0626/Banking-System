from banking.application.dto.auth.register_dto import (
    RegisterCustomerRequest,
    RegisterCustomerResult,
)
from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.application.ports.security.password_hasher import PasswordHasher
from banking.domain.entities.customer import Customer
from banking.domain.exceptions.customer_exceptions import (
    DuplicateMobileException,
    DuplicateNationalIdException,
    DuplicateUsernameException,
)
from banking.domain.value_objects.email import Email
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.password import Password
from banking.domain.value_objects.phone_number import PhoneNumber


class RegisterCustomer:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        password_hasher: PasswordHasher,
        password_strict_mode: bool = False,
    ) -> None:
        self._customers = customer_repository
        self._hasher = password_hasher
        self._strict = password_strict_mode

    def execute(self, request: RegisterCustomerRequest) -> RegisterCustomerResult:
        """Registers a new customer in the system."""
        national_id = NationalId(request.national_id)
        phone_number = PhoneNumber(request.mobile)
        email = Email(request.email)
        password = Password(plain_value=request.password, strict=self._strict)

        if self._customers.get_by_national_id(national_id.value) is not None:
            raise DuplicateNationalIdException(
                f"National ID {national_id.value} is already registered."
            )

        if self._customers.get_by_mobile(phone_number.value) is not None:
            raise DuplicateMobileException(
                f"Phone number {phone_number.value} is already registered."
            )

        if self._customers.get_by_username(request.username) is not None:
            raise DuplicateUsernameException(f"Username {request.username} is already in use.")

        hashed_password = self._hasher.hash(password.plain_value)

        customer = Customer(
            id=None,
            first_name=request.first_name,
            last_name=request.last_name,
            national_id=national_id,
            mobile=phone_number,
            email=email.value,
            username=request.username,
            password_hash=hashed_password,
            is_active=True,
            is_restricted=False,
        )

        saved_customer = self._customers.add(customer)
        if saved_customer.id is None:
            raise RuntimeError("Customer repository did not assign an ID.")

        return RegisterCustomerResult(
            customer_id=saved_customer.id.value, username=saved_customer.username
        )
