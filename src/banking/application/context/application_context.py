from dataclasses import dataclass
from typing import Any

from banking.application.context.session_context import Session
from banking.domain.exceptions.auth_exceptions import AuthenticationFailedException


@dataclass
class ApplicationContext:
    """Registry of use cases and holder of the current session (PRD 43.1)."""

    use_cases: dict[str, Any]
    current_session: Session | None = None

    def get_use_case(self, name: str) -> Any:
        """Return a registered use case or fail loudly if the name is unknown."""
        if name not in self.use_cases:
            raise KeyError(f"UseCase '{name}' is not registered in the container.")
        return self.use_cases[name]

    @property
    def is_authenticated(self) -> bool:
        """True while a valid, non-invalidated session exists."""
        return self.current_session is not None and self.current_session.is_active

    def start_session(self, session: Session) -> None:
        """Store the session created by a successful login."""
        self.current_session = session

    def end_session(self) -> None:
        """Invalidate and forget the current session (safe to call when logged out)."""
        if self.current_session is not None:
            self.current_session.invalidate()
        self.current_session = None

    def require_session(self) -> Session:
        """Return the active session or raise AuthenticationFailed."""
        if self.current_session is None or not self.current_session.is_active:
            raise AuthenticationFailedException("You must log in to perform this operation.")
        return self.current_session
