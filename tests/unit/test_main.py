import importlib
import runpy
import sys
from types import ModuleType, SimpleNamespace


def test_main_builds_and_runs_console(monkeypatch):
    factory_module = ModuleType("banking.infrastructure.bootstrap.application_factory")
    factory_module.create_application = lambda: None
    monkeypatch.setitem(
        sys.modules,
        "banking.infrastructure.bootstrap.application_factory",
        factory_module,
    )
    console_module = ModuleType("banking.presentation.console.console_factory")
    console_module.build_console = lambda app: SimpleNamespace(run=lambda: None)
    monkeypatch.setitem(sys.modules, "banking.presentation.console.console_factory", console_module)
    monkeypatch.delitem(sys.modules, "banking.main", raising=False)
    main = importlib.import_module("banking.main")

    app = SimpleNamespace()
    factory_calls = []
    run_calls = []

    def create_application():
        factory_calls.append(True)
        return app

    def build_console(application):
        assert application is app
        return SimpleNamespace(run=lambda: run_calls.append(True))

    monkeypatch.setattr(main, "create_application", create_application)
    monkeypatch.setattr(main, "build_console", build_console)

    main.main()

    assert factory_calls == [True]
    assert run_calls == [True]


def test_script_entry_point_invokes_main(monkeypatch):
    factory_module = ModuleType("banking.infrastructure.bootstrap.application_factory")
    factory_module.create_application = lambda: SimpleNamespace()
    monkeypatch.setitem(
        sys.modules,
        "banking.infrastructure.bootstrap.application_factory",
        factory_module,
    )
    run_calls = []
    console_module = ModuleType("banking.presentation.console.console_factory")
    console_module.build_console = lambda app: SimpleNamespace(run=lambda: run_calls.append(True))
    monkeypatch.setitem(sys.modules, "banking.presentation.console.console_factory", console_module)

    runpy.run_path("src/banking/main.py", run_name="__main__")

    assert run_calls == [True]
