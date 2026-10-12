import re

import pytest

from banking.infrastructure.generators.account_number_generator import RandomAccountNumberGenerator
from banking.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from banking.infrastructure.security.in_memory_rate_limiter import InMemoryRateLimiter


def test_random_account_number_is_sixteen_digits_and_does_not_start_with_zero():
    number = RandomAccountNumberGenerator().generate()

    assert re.fullmatch(r"[1-9]\d{15}", number)


@pytest.mark.parametrize("rounds", [4])
def test_password_hasher_hashes_and_verifies_password(rounds):
    hasher = BcryptPasswordHasher(rounds=rounds)
    hashed = hasher.hash("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert hasher.verify("correct horse battery staple", hashed)
    assert not hasher.verify("incorrect", hashed)


def test_password_hasher_returns_false_for_malformed_hash():
    assert BcryptPasswordHasher(rounds=4).verify("password", "not-a-bcrypt-hash") is False


def test_rate_limiter_locks_after_threshold_and_expires_lock():
    now = [100.0]
    limiter = InMemoryRateLimiter(
        max_attempts=2, window_seconds=10, lock_seconds=5, clock=lambda: now[0]
    )

    assert limiter.is_locked("alice") is False
    limiter.register_failure("alice")
    assert limiter.is_locked("alice") is False
    limiter.register_failure("alice")
    assert limiter.is_locked("alice") is True

    now[0] = 104.99
    assert limiter.is_locked("alice") is True
    now[0] = 105.0
    assert limiter.is_locked("alice") is False


def test_rate_limiter_uses_sliding_window_and_keeps_keys_independent():
    now = [0.0]
    limiter = InMemoryRateLimiter(
        max_attempts=2, window_seconds=10, lock_seconds=30, clock=lambda: now[0]
    )
    limiter.register_failure("alice")
    now[0] = 10.01
    limiter.register_failure("alice")

    assert not limiter.is_locked("alice")
    limiter.register_failure("bob")
    assert not limiter.is_locked("bob")


def test_rate_limiter_reset_clears_failures_and_active_lock():
    now = [1.0]
    limiter = InMemoryRateLimiter(
        max_attempts=1, window_seconds=10, lock_seconds=30, clock=lambda: now[0]
    )
    limiter.register_failure("alice")
    assert limiter.is_locked("alice")

    limiter.reset("alice")

    assert not limiter.is_locked("alice")
    limiter.register_failure("alice")
    assert limiter.is_locked("alice")
