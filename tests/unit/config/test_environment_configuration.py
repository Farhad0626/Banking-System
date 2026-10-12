from decimal import Decimal

import pytest

from banking.infrastructure.configuration.environment_configuration import (
    ConfigurationError,
    EnvironmentConfiguration,
)


def test_override_takes_precedence_over_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "environment")
    config = EnvironmentConfiguration({"APP_NAME": "override"})
    assert config.get_str("APP_NAME") == "override"


def test_getters_use_environment_values_and_defaults(monkeypatch):
    monkeypatch.setenv("APP_COUNT", "42")
    monkeypatch.setenv("APP_RATE", "0.125")
    monkeypatch.setenv("APP_ENABLED", " YES ")
    monkeypatch.setenv("APP_DISABLED", "off")
    monkeypatch.delenv("APP_NAME", raising=False)

    config = EnvironmentConfiguration()

    assert config.get_int("APP_COUNT") == 42
    assert config.get_decimal("APP_RATE") == Decimal("0.125")
    assert config.get_bool("APP_ENABLED") is True
    assert config.get_bool("APP_DISABLED", default=True) is False
    assert config.get_str("APP_NAME", "default") == "default"
    assert config.get_bool("MISSING_FLAG") is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1", True),
        ("TRUE", True),
        ("yes", True),
        ("On", True),
        ("0", False),
        ("FALSE", False),
        ("no", False),
        ("Off", False),
    ],
)
def test_get_bool_accepts_supported_spellings(raw, expected):
    config = EnvironmentConfiguration({"FEATURE": raw})
    assert config.get_bool("FEATURE") is expected


@pytest.mark.parametrize(
    ("getter", "raw", "message"),
    [
        ("get_int", "1.5", "integer"),
        ("get_decimal", "invalid", "decimal number"),
        ("get_bool", "sometimes", "true or false"),
    ],
)
def test_invalid_environment_value_raises_configuration_error(getter, raw, message):
    config = EnvironmentConfiguration({"SETTING": raw})

    with pytest.raises(ConfigurationError, match=message):
        getattr(config, getter)("SETTING")


@pytest.mark.parametrize("getter", ["get_str", "get_int", "get_decimal"])
def test_missing_required_setting_raises_configuration_error(getter):
    config = EnvironmentConfiguration({})

    with pytest.raises(ConfigurationError, match="SETTING.*not defined"):
        getattr(config, getter)("SETTING")


def test_empty_override_is_treated_as_missing_and_default_is_used(monkeypatch):
    monkeypatch.delenv("EMPTY_SETTING", raising=False)
    config = EnvironmentConfiguration({"EMPTY_SETTING": ""})

    assert config.get_str("EMPTY_SETTING", "fallback") == "fallback"
