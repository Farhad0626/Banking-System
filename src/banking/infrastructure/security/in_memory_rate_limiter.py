import logging
import threading
import time
from collections import deque
from collections.abc import Callable

from banking.application.ports.security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class InMemoryRateLimiter(RateLimiter):
    """Locks a key for a fixed duration after too many failures inside a sliding time window."""

    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        lock_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Configure thresholds; the clock is injectable so tests can control time."""
        self._max = max_attempts
        self._window = window_seconds
        self._lock_duration = lock_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._mutex = threading.Lock()

    def is_locked(self, key: str) -> bool:
        """Return True while the key is locked; expired locks are cleared automatically."""
        with self._mutex:
            until = self._locked_until.get(key)
            if until is None:
                return False
            if self._clock() >= until:
                del self._locked_until[key]
                self._failures.pop(key, None)
                return False
            return True

    def register_failure(self, key: str) -> None:
        """Record a failed attempt and lock the key when the threshold is reached within the window."""
        with self._mutex:
            now = self._clock()
            attempts = self._failures.setdefault(key, deque())
            attempts.append(now)
            while attempts and now - attempts[0] > self._window:
                attempts.popleft()
            if len(attempts) >= self._max:
                self._locked_until[key] = now + self._lock_duration
                logger.warning(
                    "Login locked for user=%s after %d failed attempts", key, len(attempts)
                )

    def reset(self, key: str) -> None:
        """Clear failures and any lock for the key (called after a successful login)."""
        with self._mutex:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)
