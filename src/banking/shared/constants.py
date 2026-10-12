"""System-wide constants shared by the presentation layer."""

APP_TITLE = "Banking System"

ACCOUNT_TYPE_LABELS: tuple[tuple[str, str], ...] = (
    ("SAVINGS", "Savings"),
    ("CHECKING", "Checking"),
    ("TERM_DEPOSIT", "Term Deposit"),
)
TRANSACTION_TYPES: tuple[str, ...] = ("DEPOSIT", "WITHDRAWAL", "TRANSFER")

HISTORY_DISPLAY_LIMIT = 10
