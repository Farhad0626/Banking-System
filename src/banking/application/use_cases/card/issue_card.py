from typing import Any


class IssueCard:
    def execute(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("It is outside the core release.")
