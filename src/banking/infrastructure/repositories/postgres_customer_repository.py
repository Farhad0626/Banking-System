from typing import Any

from psycopg import errors

from banking.application.ports.repositories.customer_repository import CustomerRepository
from banking.domain.entities.customer import Customer
from banking.domain.exceptions.customer_exceptions import (
    CustomerNotFoundException,
    DuplicateMobileException,
    DuplicateNationalIdException,
    DuplicateUsernameException,
)
from banking.domain.exceptions.domain_exception import DomainException
from banking.domain.value_objects.customer_id import CustomerId
from banking.domain.value_objects.national_id import NationalId
from banking.domain.value_objects.phone_number import PhoneNumber
from banking.infrastructure.repositories.postgres_repository_base import PostgresRepositoryBase

_COLUMNS = (
    "id, first_name, last_name, national_id, mobile, email, username, "
    "password_hash, is_active, is_restricted, created_at, updated_at, deleted_at"
)

_UNIQUE_VIOLATIONS: dict[str, tuple[type[DomainException], str]] = {
    "customers_national_id_key": (
        DuplicateNationalIdException,
        "National ID is already registered.",
    ),
    "customers_mobile_key": (DuplicateMobileException, "Mobile number is already registered."),
    "customers_username_key": (DuplicateUsernameException, "Username is already in use."),
}


def _escape_like(keyword: str) -> str:
    """Escape LIKE wildcards (% and _) and backslashes so user input is matched literally."""
    return keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _to_customer(row: dict[str, Any]) -> Customer:
    """Map a database row to a Customer entity."""
    return Customer(
        id=CustomerId(row["id"]),
        first_name=row["first_name"],
        last_name=row["last_name"],
        national_id=NationalId(row["national_id"]),
        mobile=PhoneNumber(row["mobile"]),
        email=row["email"],
        username=row["username"],
        password_hash=row["password_hash"],
        is_active=row["is_active"],
        is_restricted=row["is_restricted"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
    )


class PostgresCustomerRepository(PostgresRepositoryBase, CustomerRepository):
    """Stores customers in PostgreSQL, hides soft-deleted rows and maps unique violations to domain exceptions."""

    def add(self, customer: Customer) -> Customer:
        """Insert a new customer and fill in its generated id and timestamps."""
        sql = """
            INSERT INTO customers
                (first_name, last_name, national_id, mobile, email, username,
                 password_hash, is_active, is_restricted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        params = (
            customer.first_name,
            customer.last_name,
            customer.national_id.value,
            customer.mobile.value,
            customer.email,
            customer.username,
            customer.password_hash,
            customer.is_active,
            customer.is_restricted,
        )
        try:
            row = self._fetch_one(sql, params)
        except errors.UniqueViolation as exc:
            constraint_name = exc.diag.constraint_name
            if constraint_name is not None and constraint_name in _UNIQUE_VIOLATIONS:
                exc_class, message = _UNIQUE_VIOLATIONS[constraint_name]
                raise exc_class(message) from exc
            raise
        if row is None:
            raise RuntimeError("Customer insert returned no row.")
        customer.id = CustomerId(row["id"])
        customer.created_at = row["created_at"]
        customer.updated_at = row["updated_at"]
        return customer

    def _get_one(self, column: str, value: object) -> Customer | None:
        """Fetch one non-deleted customer by an internal column name (never user input)."""
        row = self._fetch_one(
            f"SELECT {_COLUMNS} FROM customers WHERE {column} = %s AND deleted_at IS NULL", (value,)
        )
        return _to_customer(row) if row else None

    def get_by_id(self, customer_id: int) -> Customer | None:
        """Return the customer with the given id, or None."""
        return self._get_one("id", customer_id)

    def get_by_username(self, username: str) -> Customer | None:
        """Return the customer with the given username, or None."""
        return self._get_one("username", username)

    def get_by_national_id(self, national_id: str) -> Customer | None:
        """Return the customer with the given national id, or None."""
        return self._get_one("national_id", national_id)

    def get_by_mobile(self, mobile: str) -> Customer | None:
        """Return the customer with the given mobile number, or None."""
        return self._get_one("mobile", mobile)

    def search(self, keyword: str | None = None) -> list[Customer]:
        """List customers, optionally filtered by a literal keyword across name, ids, mobile and username."""
        if not keyword:
            rows = self._fetch_all(
                f"SELECT {_COLUMNS} FROM customers WHERE deleted_at IS NULL ORDER BY id"
            )
        else:
            pattern = f"%{_escape_like(keyword)}%"
            rows = self._fetch_all(
                f"""
                SELECT {_COLUMNS} FROM customers
                WHERE deleted_at IS NULL
                  AND (first_name ILIKE %s OR last_name ILIKE %s OR national_id ILIKE %s
                       OR mobile ILIKE %s OR username ILIKE %s)
                ORDER BY id
                """,
                (pattern,) * 5,
            )
        return [_to_customer(row) for row in rows]

    def update(self, customer: Customer) -> None:
        """Persist changes to an existing customer; raises CustomerNotFound if the row does not exist."""
        if customer.id is None:
            raise CustomerNotFoundException("Customer without an ID cannot be updated.")
        affected = self._execute(
            """
            UPDATE customers
               SET first_name = %s, last_name = %s, mobile = %s, email = %s,
                   password_hash = %s, is_active = %s, is_restricted = %s, deleted_at = %s
             WHERE id = %s
            """,
            (
                customer.first_name,
                customer.last_name,
                customer.mobile.value,
                customer.email,
                customer.password_hash,
                customer.is_active,
                customer.is_restricted,
                customer.deleted_at,
                customer.id.value,
            ),
        )
        if affected == 0:
            raise CustomerNotFoundException(f"Customer with ID {customer.id.value} was not found.")

    def delete(self, customer_id: int) -> None:
        """Soft-delete a customer so historical records remain linked to the customer."""
        affected = self._execute(
            """
            UPDATE customers
               SET is_active = FALSE, deleted_at = now()
             WHERE id = %s AND deleted_at IS NULL
            """,
            (customer_id,),
        )
        if affected == 0:
            raise CustomerNotFoundException(f"Customer with ID {customer_id} was not found.")
