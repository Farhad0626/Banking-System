from collections.abc import Callable
from dataclasses import dataclass

from banking.application.context.application_context import ApplicationContext
from banking.presentation.console.error_handler import ErrorHandler
from banking.presentation.console.input_reader import InputReader
from banking.presentation.console.output_writer import OutputWriter


@dataclass(frozen=True)
class MenuOption:
    """A numbered menu entry; its handler returns True to leave the current menu."""

    label: str
    handler: Callable[[], bool | None]


class BaseMenu:
    """Base class giving every menu the same collaborators and a guarded menu loop."""

    def __init__(
        self,
        app: ApplicationContext,
        reader: InputReader,
        writer: OutputWriter,
        errors: ErrorHandler,
    ) -> None:
        """Store the collaborators every menu needs."""
        self._app = app
        self._reader = reader
        self._writer = writer
        self._errors = errors

    def _run_loop(
        self,
        title: str,
        options: list[MenuOption],
        keep_running: Callable[[], bool] = lambda: True,
    ) -> None:
        """Show the menu repeatedly, running the chosen handler inside the error guard."""
        numbers = [str(number) for number in range(1, len(options) + 1)]
        while keep_running():
            self._writer.menu(title, [option.label for option in options])
            choice = self._reader.read_choice("Select an option", numbers)
            option = options[int(choice) - 1]
            with self._errors.guard():
                if option.handler():
                    return
