import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

_SENSITIVE_PATTERN = re.compile(
    r"(?i)\b(password|password_hash|pin|pin_hash|national_id|secret|token|db_password)\b(\s*[=:]\s*)(\S+)"
)
_HANDLER_NAME = "banking_file_handler"


class SensitiveDataFilter(logging.Filter):
    """Masks the values of sensitive fields (passwords, hashes, national IDs, tokens) in log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive key=value pairs in the formatted message and always keep the record."""
        record.msg = _SENSITIVE_PATTERN.sub(r"\1\2***", record.getMessage())
        record.args = ()
        return True


def setup_logging(level: str = "INFO", file_path: str = "logs/app.log") -> None:
    """Configure a rotating file handler on the root logger once (safe to call repeatedly)."""
    root = logging.getLogger()
    if any(handler.get_name() == _HANDLER_NAME for handler in root.handlers):
        return

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    handler.addFilter(SensitiveDataFilter())

    root.setLevel(level.upper())
    root.addHandler(handler)
