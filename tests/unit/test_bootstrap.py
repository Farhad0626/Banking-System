"""Tests for loading database settings."""

import pytest

from banking.config.settings import get_db_config


def test_db_config_uses_defaults_when_environment_is_unset(monkeypatch):
    for name in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    config = get_db_config()
    assert config == {
        "host": "localhost",
        "port": 5432,
        "dbname": "banking_system",
        "user": "",
        "password": "",
    }


def test_db_config_reads_environment_and_converts_port(monkeypatch):
    monkeypatch.setenv("DB_HOST", "db.example.test")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "test_banking")
    monkeypatch.setenv("DB_USER", "tester")
    monkeypatch.setenv("DB_PASSWORD", "secret")

    config = get_db_config()
    assert config == {
        "host": "db.example.test",
        "port": 6543,
        "dbname": "test_banking",
        "user": "tester",
        "password": "secret",
    }


def test_db_config_rejects_non_integer_port(monkeypatch):
    monkeypatch.setenv("DB_PORT", "not-a-port")
    with pytest.raises(ValueError):
        get_db_config()
