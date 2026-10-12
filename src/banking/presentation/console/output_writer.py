from collections.abc import Callable, Sequence


class OutputWriter:
    """Formats and prints console output; the print function is injectable for tests."""

    def __init__(self, print_fn: Callable[..., None] = print) -> None:
        """Store the function used to emit each line."""
        self._print = print_fn

    def blank(self) -> None:
        """Print an empty line."""
        self._print()

    def title(self, text: str) -> None:
        """Print a framed section title."""
        line = "=" * max(len(text) + 4, 30)
        self._print()
        self._print(line)
        self._print(f"  {text}")
        self._print(line)

    def menu(self, title: str, options: Sequence[str]) -> None:
        """Print a numbered menu."""
        self._print()
        self._print(f"--- {title} ---")
        for number, label in enumerate(options, start=1):
            self._print(f"  {number}. {label}")

    def success(self, message: str) -> None:
        """Print a success message."""
        self._print(f"[OK] {message}")

    def error(self, message: str) -> None:
        """Print an error message."""
        self._print(f"[ERROR] {message}")

    def info(self, message: str) -> None:
        """Print an informational message."""
        self._print(f"[INFO] {message}")

    def key_values(self, items: Sequence[tuple[str, str]]) -> None:
        """Print aligned 'label : value' lines."""
        width = max((len(label) for label, _ in items), default=0)
        for label, value in items:
            self._print(f"  {label.ljust(width)} : {value}")

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
        """Print a left-aligned text table with a header separator."""
        widths = [len(header) for header in headers]
        for row in rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], len(str(cell)))

        def render(cells: Sequence[object]) -> str:
            return " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(cells))

        self._print(render(headers))
        self._print("-+-".join("-" * width for width in widths))
        for row in rows:
            self._print(render(row))
