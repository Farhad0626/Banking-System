from banking.presentation.console.base_menu import BaseMenu
from banking.presentation.console.view_formatters import customer_lines


class CustomerMenu(BaseMenu):
    """Shows the logged-in customer's profile."""

    def show_profile(self) -> None:
        """Display the profile of the customer in the current session."""
        session = self._app.require_session()
        customer = self._app.get_use_case("get_customer").execute(session.customer_id, session)
        self._writer.title("Customer Profile")
        self._writer.key_values(customer_lines(customer))
