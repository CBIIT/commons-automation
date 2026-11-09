"""Navigation helper checks against a local HTTP fixture; no external sites."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from unittest.mock import Mock

import openpyxl
import pytest

from Commons.apps.ccdi import CCDI
from Commons.browser_actions import Ui
from Commons.excel_testcase.registry import profile_for_case_path
from Commons.suite_config import suite_markers_for_excel_case

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def control_site():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/right")
                self.end_headers()
                return
            self.send_response(404 if self.path == "/missing" else 200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            body = '''<html><head><title>Local navigation fixture</title></head><body>
                <h1 class="introTextTitle1">Home navigation fixture</h1>
                <a id="good" href="/right">Good</a>
                <a id="wrong" href="/right" onclick="event.preventDefault();location.href='/wrong'">Wrong</a>
                <a id="redirect" href="/redirect" target="_blank">Redirect</a>
                <a id="missing" href="/missing" target="_blank">Missing</a>
                <a id="export" href="/right" target="_blank" style="display:block;width:0;height:30px">
                  <img class="exportIcon" width="20" height="20" alt="Export"
                    src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==">
                </a>
                </body></html>'''
            self.wfile.write(body.encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


@pytest.fixture
def functional_app(page, control_site, tmp_path):
    app = CCDI.__new__(CCDI)
    app.page = page
    app.settings = SimpleNamespace(url=control_site + "/home", env="qa")
    app.repo = Mock()
    app.repo.xpath.side_effect = lambda key: "//h1" if key.startswith("Static/") else f"//a[@id='{key}']"
    app.ui = Ui(page, 1000)
    app.output_dir = tmp_path
    app.failures = []
    app.results = []
    app.CONTROL_TIMEOUT_MS = 1000
    page.goto(app.settings.url)
    return app


def test_wrong_destination_fails_even_when_href_is_correct(functional_app, control_site):
    functional_app.verify_link_navigation("wrong", control_site + "/right")
    assert functional_app.failures
    assert functional_app._control_checks[0][3] == "FAILED"
    assert functional_app.page.url == control_site + "/home"
    functional_app.failures.clear()  # The framework otherwise fails expected-negative fixtures.


def test_verified_redirect_passes_and_new_tab_is_closed(functional_app, control_site):
    functional_app.verify_link_navigation("redirect", control_site + "/redirect")
    assert not functional_app.failures
    assert "HTTP redirect verified" in functional_app._control_checks[0][2]
    assert len(functional_app.page.context.pages) == 1


def test_configured_spa_landing_is_verified_explicitly(functional_app, control_site):
    functional_app.verify_link_navigation("wrong", control_site + "/right => " + control_site + "/wrong")
    assert not functional_app.failures
    assert functional_app._control_checks[0][2] == control_site + "/wrong"


def test_export_icon_inside_zero_width_anchor_is_clicked(functional_app, control_site):
    assert functional_app.page.locator("#export").bounding_box()["width"] == 0
    functional_app.verify_link_navigation("export", control_site + "/right")
    assert not functional_app.failures
    assert functional_app._control_checks[0][3] == "PASSED"
    assert len(functional_app.page.context.pages) == 1


def test_email_navigation_is_rejected_without_opening_a_tab(functional_app):
    functional_app.verify_link_navigation("good", "mailto:someone@example.org")
    assert "email/signup are excluded" in functional_app.failures[0]
    assert len(functional_app.page.context.pages) == 1
    functional_app.failures.clear()



def test_http_error_fails_and_following_link_still_runs(functional_app, control_site):
    functional_app.verify_link_navigation("missing", control_site + "/missing")
    functional_app.verify_link_navigation("good", control_site + "/right")
    assert "HTTP 404" in functional_app.failures[0]
    assert [row[3] for row in functional_app._control_checks] == ["FAILED", "PASSED"]
    assert len(functional_app.page.context.pages) == 1
    functional_app.failures.clear()


@pytest.mark.parametrize("actual,expected", [
    ("https://wrong.example/about", "https://ccdi-qa.cancer.gov/about"),
    ("https://ccdi-qa.cancer.gov/news#wrong", "https://ccdi-qa.cancer.gov/news#right"),
    ("https://ccdi-qa.cancer.gov/search?q=wrong", "https://ccdi-qa.cancer.gov/search?q=right"),
])
def test_destination_comparison_rejects_wrong_host_fragment_and_query(actual, expected):
    assert not CCDI._control_url_matches(actual, expected)


def test_functional_case_is_discoverable_and_does_not_invoke_static_checks():
    path = ROOT / "Testcases/CCDI/functional/TC01_CCDI_Verify_HomePage_Controls.xlsx"
    assert profile_for_case_path(path).fixture == "ccdi"
    assert suite_markers_for_excel_case(path) == frozenset()
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        rows = list(wb["Steps"].values)[2:]
        assert all(row[1] not in ("verify_static_data", "verify_home_page", "verify_home_controls") for row in rows)
        assert all(not str(row[4] or "").lower().startswith("mailto:") for row in rows)
        assert sum(row[1] in ("verify_link_navigation", "verify_carousel_link", "verify_home_control_action") for row in rows) == 79
    finally:
        wb.close()
