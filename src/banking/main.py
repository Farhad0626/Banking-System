import sys

from banking.infrastructure.bootstrap.application_factory import create_application
from banking.presentation.console.console_factory import build_console


def _configure_console_encoding() -> None:
    """Use UTF-8 for console output so Persian messages can never crash the app."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    """Create the application and run the console menus until the user exits."""
    _configure_console_encoding()
    app = create_application()
    build_console(app).run()


if __name__ == "__main__":
    main()
