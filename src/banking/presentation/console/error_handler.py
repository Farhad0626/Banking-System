import logging
from collections.abc import Iterator
from contextlib import contextmanager

from banking.domain.exceptions.domain_exception import DomainException
from banking.presentation.console.input_reader import InputCancelled
from banking.presentation.console.output_writer import OutputWriter

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "An unexpected error occurred. Please try again."


class ErrorHandler:
    """Shows domain/validation errors as-is and hides unexpected ones behind a generic message."""

    def __init__(self, writer: OutputWriter) -> None:
        """Store the writer used to display errors."""
        self._writer = writer

    def report(self, error: Exception) -> None:
        """Display an error; unexpected errors are logged with their traceback, not shown."""
        if isinstance(error, (DomainException, ValueError)):
            self._writer.error(str(error))
        else:
            logger.error("Unexpected error in console action", exc_info=error)
            self._writer.error(GENERIC_ERROR_MESSAGE)

    @contextmanager
    def guard(self) -> Iterator[None]:
        """Run an action and report any error instead of crashing (InputCancelled still propagates)."""
        try:
            yield
        except InputCancelled:
            raise
        except Exception as error:  # noqa: BLE001
            self.report(error)
