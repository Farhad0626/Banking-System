from banking.application.context.application_context import ApplicationContext
from banking.presentation.console.auth_menu import AuthMenu
from banking.presentation.console.base_menu import BaseMenu, MenuOption
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputCancelled, InputReader
from banking.presentation.console.output_writer import OutputWriter
from banking.shared.constants import APP_TITLE


class MainMenu(BaseMenu):
    """Register / Login / Exit; also guarantees the session is closed when the program ends."""

    def __init__(
        self,
        app: ApplicationContext,
        reader: InputReader,
        writer: OutputWriter,
        errors: ErrorHandler,
        auth_menu: AuthMenu,
    ) -> None:
        """Keep the authentication menu used for register/login and the logged-in menu."""
        super().__init__(app, reader, writer, errors)
        self._auth = auth_menu

    def run(self) -> None:
        """Run until the user exits, presses Ctrl+C or input ends."""
        self._writer.title(APP_TITLE)
        options = [
            MenuOption("Register", self._auth.register),
            MenuOption("Login", self._login),
            MenuOption("Exit", lambda: True),
        ]
        try:
            self._run_loop("Main Menu", options)
        except KeyboardInterrupt, InputCancelled:
            self._writer.blank()
        finally:
            self._app.end_session()
            self._writer.info("Goodbye!")

    def _login(self) -> None:
        """Log in and, on success, hand control to the logged-in menu."""
        if self._auth.login():
            self._auth.run()
