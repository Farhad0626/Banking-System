import pytest

from banking.application.context.application_context import ApplicationContext


def test_get_use_case_returns_registered_instance():
    use_case = object()
    context = ApplicationContext({"login": use_case})

    assert context.get_use_case("login") is use_case


def test_get_use_case_raises_clear_key_error_for_unknown_name():
    context = ApplicationContext({})

    with pytest.raises(KeyError, match=r"UseCase 'missing' is not registered in the container"):
        context.get_use_case("missing")
