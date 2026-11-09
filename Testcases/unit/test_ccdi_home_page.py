"""CCDI static testcase scope and failure handling without a browser or database."""
from pathlib import Path
from unittest.mock import Mock

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from Commons.apps.ccdi import CCDI
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("filename,steps", [
    ("TC01_CCDI_Verify_HomePage_Data.xlsx", [
        ("accept_banner", (), {}),
        ("click", ("Navbar/Home-Btn",), {}),
        ("verify_home_page", (), {}),
        ("verify_home_controls", (), {}),
        ("assert_no_failures", (), {}),
    ]),
    ("TC02_CCDI_Verify_AboutPage_Data.xlsx", [
        ("accept_banner", (), {}),
        ("click", ("Navbar/About-Btn",), {}),
        ("click", ("Navbar/About-AboutCCDI-Btn",), {}),
        ("verify_about_page_data", (), {}),
        ("assert_no_failures", (), {}),
    ]),
    ("TC03_CCDI_Verify_ResourcesPage_Data.xlsx", [
        ("accept_banner", (), {}),
        ("click", ("Navbar/Home-Btn",), {}),
        ("click", ("Navbar/Resources-Btn",), {}),
        ("verify_static_data", ("ResourcesPage",), {}),
        ("assert_no_failures", (), {}),
    ]),
])
def test_page_excel_executes_the_visible_steps_in_order(filename, steps):
    app = Mock(spec=CCDI)
    run_testcase_excel(app, ROOT / "Testcases/CCDI/static" / filename)
    assert app.method_calls == steps


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

    app.verify_home_controls()

    assert len(app.failures) == 2
    assert "HeaderSearchInput" in app.failures[0]
    assert "FooterEmailInput" in app.failures[1]
    assert app.results[-1]["check"] == "Home control FooterSignUpButton"
    assert app.results[-1]["status"] == "PASSED"
    with pytest.raises(AssertionError, match="2 check.*failed"):
        app.assert_no_failures()
