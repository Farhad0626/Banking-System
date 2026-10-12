import logging

from banking.domain.exceptions.domain_exception import DomainException
from banking.presentation.console.error_handler import (
    GENERIC_ERROR_MESSAGE,
    ErrorHandler,
)
from banking.presentation.console.input_reader import InputCancelled
from banking.presentation.console.output_writer import OutputWriter


def test_output_writer_formats_messages_menus_key_values_and_tables() -> None:
    output: list[str] = []

    def capture(*values: object) -> None:
        output.append(" ".join(map(str, values)))

    writer = OutputWriter(capture)

    writer.success("Saved")
    writer.error("Invalid")
    writer.info("Ready")
    writer.menu("Main", ["Login", "Exit"])
    writer.key_values([("ID", "4"), ("Customer", "Ada")])
    writer.table(["ID", "Name"], [[1, "Ada"], [20, "Grace"]])

    assert output == [
        "[OK] Saved",
        "[ERROR] Invalid",
        "[INFO] Ready",
        "",
        "--- Main ---",
        "  1. Login",
        "  2. Exit",
        "  ID       : 4",
        "  Customer : Ada",
        "ID | Name ",
        "---+------",
        "1  | Ada  ",
        "20 | Grace",
    ]


def test_error_handler_shows_domain_errors_and_logs_unexpected_errors(caplog) -> None:
    output: list[str] = []
    handler = ErrorHandler(OutputWriter(lambda *values: output.append(" ".join(map(str, values)))))

    handler.report(DomainException("Not allowed"))
    with caplog.at_level(logging.ERROR, logger="banking.presentation.console.error_handler"):
        handler.report(RuntimeError("internal detail"))

    assert output == [
        "[ERROR] Not allowed",
        f"[ERROR] {GENERIC_ERROR_MESSAGE}",
    ]
    assert "internal detail" in caplog.text


def test_guard_reports_errors_and_does_not_swallow_input_cancellation() -> None:
    output: list[str] = []
    handler = ErrorHandler(OutputWriter(lambda *values: output.append(" ".join(map(str, values)))))

    with handler.guard():
        raise ValueError("Invalid amount")

    assert output == ["[ERROR] Invalid amount"]
    try:
        with handler.guard():
            raise InputCancelled
    except InputCancelled:
        pass
    else:
        raise AssertionError("InputCancelled must propagate from the guard")
