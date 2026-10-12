from banking.application.context.session_context import Session


class Logout:
    """Ends the current session so protected use cases reject it afterwards."""

    def execute(self, session: Session | None = None) -> None:
        """Invalidate the given session (no-op when there is none)."""
        if session is not None:
            session.invalidate()
