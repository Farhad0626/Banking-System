import logging

from banking.infrastructure.logging.logger import get_logger
from banking.infrastructure.logging.logging_config import SensitiveDataFilter, setup_logging
from banking.infrastructure.notifications.console_notification import ConsoleNotificationSender


def test_console_notification_sender_prints_recipient_and_message(capsys):
    ConsoleNotificationSender().send("user@example.test", "Your transfer completed")

    assert capsys.readouterr().out == (
        "[NOTIFICATION] -> user@example.test: Your transfer completed\n"
    )


def test_get_logger_returns_named_logger():
    assert get_logger("banking.tests") is logging.getLogger("banking.tests")


def test_sensitive_data_filter_masks_sensitive_values():
    record = logging.LogRecord(
        "banking.tests",
        logging.INFO,
        __file__,
        1,
        "password=%s national_id=1234567890 token=abc",
        ("p@ssword",),
        None,
    )

    assert SensitiveDataFilter().filter(record) is True
    assert record.getMessage() == "password=*** national_id=*** token=***"
    assert record.args == ()


def test_setup_logging_creates_file_handler_once(tmp_path, monkeypatch):
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    old_level = root.level
    root.handlers.clear()
    try:
        log_path = tmp_path / "nested" / "banking.log"
        setup_logging("DEBUG", str(log_path))
        handler = next(h for h in root.handlers if h.get_name() == "banking_file_handler")

        setup_logging("ERROR", str(tmp_path / "ignored.log"))

        assert handler.baseFilename == str(log_path)
        assert len([h for h in root.handlers if h.get_name() == "banking_file_handler"]) == 1
        assert root.level == logging.DEBUG
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()
        root.handlers.extend(old_handlers)
        root.setLevel(old_level)
