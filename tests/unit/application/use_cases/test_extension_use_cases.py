from importlib import import_module

import pytest


def test_issue_card_explicitly_reports_out_of_core_implementation() -> None:
    issue = import_module("banking.application.use_cases.card.issue_card").IssueCard()

    with pytest.raises(NotImplementedError, match="outside the core release"):
        issue.execute()


@pytest.mark.parametrize(
    "module_name",
    [
        "banking.application.use_cases.card.block_card",
        "banking.application.use_cases.card.unblock_card",
        "banking.application.use_cases.reporting.account_statement",
        "banking.application.use_cases.reporting.transaction_report",
    ],
)
def test_extension_point_modules_import_without_claiming_behavior(module_name: str) -> None:
    assert import_module(module_name) is not None
