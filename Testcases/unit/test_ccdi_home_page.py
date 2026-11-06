"""Home testcase scope and failure handling without a browser or database."""
from pathlib import Path
from unittest.mock import Mock

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from Commons.apps.ccdi import CCDI
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_home_excel_checks_only_home_and_asserts_results():
    app = Mock(spec=CCDI)
    run_testcase_excel(app, ROOT / "Testcases/CCDI/static/TC01_CCDI_Verify_HomePage.xlsx")
    assert app.method_calls == [
        ("verify_home_page", (), {}),
        ("assert_no_failures", (), {}),
    ]


def test_home_controls_record_all_failures_and_continue():
    app = CCDI.__new__(CCDI)
    app.failures = []
    app.results = []
    app.query_file = None
    app.repo = Mock()
    app.repo.xpath.side_effect = lambda key: key
    missing, readonly, enabled = Mock(), Mock(), Mock()
    missing.wait_for.side_effect = PlaywrightTimeoutError("not visible")
    readonly.is_enabled.return_value = True
    readonly.is_editable.return_value = False
    enabled.is_enabled.return_value = True
    app.ui = Mock()
    app.ui.loc.side_effect = [Mock(first=missing), Mock(first=readonly), Mock(first=enabled)]

    app._verify_home_controls()

    assert len(app.failures) == 2
    assert "HeaderSearchInput" in app.failures[0]
    assert "FooterEmailInput" in app.failures[1]
    assert app.results[-1]["check"] == "Home control FooterSignUpButton"
    assert app.results[-1]["status"] == "PASSED"
    with pytest.raises(AssertionError, match="2 check.*failed"):
        app.assert_no_failures()
