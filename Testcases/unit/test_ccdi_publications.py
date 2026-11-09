"""Publication tracker parsing, honest review comparisons and Excel wiring."""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from Commons.apps.ccdi import CCDI
from Commons.apps.ccdi.publications import load_release_publications, normalize, publication_urls_match, review_publications, summary_matches
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_release_updates_override_format_equivalent_ids_and_skip_drafts(monkeypatch):
    def row(status, publication_id, title, category):
        values = [status, "curator", publication_id, title, category, "CCDI Ecosystem, AI", "Report.pdf", datetime(2026, 1, 2), "January 2026", "Journal", "Journal name", 12345, "A long abstract for the publication."]
        return [SimpleNamespace(value=v, hyperlink=None, row=2) for v in values]

    class Sheet:
        def __init__(self, title, rows):
            self.title, self.rows = title, [[SimpleNamespace(value="header", row=1)]] + rows

        def iter_rows(self):
            return iter(self.rows)

    wb = Mock()
    wb.__iter__ = Mock(return_value=iter([
        Sheet("2.5.0", [row("New card", "A_01022026", "Old title", "Primary")]),
        Sheet("2.6.0", [row("Updated card", "\u2060A_01022026", "Updated title", "Secondary"), row("Potential New card", "draft", "Draft title", "Primary")]),
        Sheet("Requested- track!", [row("Submitted", "unpublished", "Not published", "Primary")]),
    ]))
    monkeypatch.setattr("Commons.apps.ccdi.publications.openpyxl.load_workbook", lambda *a, **kw: wb)
    data = load_release_publications(Path("source.xlsx"))
    assert list(data["records"]) == ["A_01022026"]
    record = data["records"]["A_01022026"]
    assert record["title"] == "Updated title"
    assert record["source_sheet"] == "2.6.0"
    assert data["counts"] == {"Secondary": 1}
    assert data["excluded"][0]["id"] == "draft"
    wb.close.assert_called_once()


@pytest.mark.parametrize("actual,expected,match", [
    ("This is the expected long abstract...", "This is the expected long abstract with more content.", True),
    ("This is a completely different abstract...", "This is the expected long abstract with more content.", False),
    ("...", "This is the expected long abstract with more content.", False),
    ("Shortened without an ellipsis", "Shortened without an ellipsis and more", False),
])
def test_summary_comparison_requires_exact_text_or_explicit_matching_truncation(actual, expected, match):
    assert summary_matches(actual, expected) is match


def test_pdf_filename_and_url_comparisons_do_not_accept_wrong_destinations():
    assert publication_urls_match("https://assets.example/Study%20report.pdf", "Study report.pdf")
    assert not publication_urls_match("https://assets.example/Wrong.pdf", "Study report.pdf")
    assert not publication_urls_match("https://wrong.example/Study.pdf", "https://right.example/Study.pdf")
    assert normalize("\ufeff\u2060ID\u00a0") == "ID"
    assert normalize("CCDI-Ecosystem") != normalize("CCDI Ecosystem")


def test_review_reports_changes_without_mutating_the_expected_baseline():
    record = {"id": "same", "title": "Paper", "category": "Primary", "date": "January 2026", "type": "Journal", "venue": "Venue", "pmid": "123", "tags": ["Old tag"], "url": "https://example.org/paper", "summary": "Summary", "source_sheet": "2.5.0", "source_row": 2}
    source = {"records": {"same": record, "missing": dict(record, id="missing")}}
    observed = {"same": dict(record, tags=["New tag"]), "new": dict(record, id="new")}
    before = deepcopy(source)
    differences = review_publications(source, observed)
    assert {(d["kind"], d["id"], d["field"]) for d in differences} == {("Field difference", "same", "tags"), ("Workbook only", "missing", "record"), ("UI only", "new", "record")}
    assert source == before


def test_pagination_does_not_accept_repeated_cards_as_complete_results():
    app = CCDI.__new__(CCDI)
    app.page = Mock()
    app._publication_count = Mock(return_value=2)
    app._read_publication_page = Mock(return_value=[{"id": "duplicate"}, {"id": "duplicate"}])
    with pytest.raises(AssertionError, match="Repeated publication"):
        app._collect_publication_pages()


def test_publication_excel_exposes_navigation_and_loads_source_explicitly():
    app = Mock(spec=CCDI)
    path = ROOT / "Testcases/CCDI/functional/TC02_CCDI_Verify_PublicationsPage_Controls.xlsx"
    run_testcase_excel(app, path)
    assert app.method_calls[:4] == [call.accept_banner(), call.click("Navbar/About-Btn"), call.click("Navbar/About-Publications-Btn"), call.load_publications_source("publications/CCDISupportedPublications.xlsx")]
    assert app.verify_publications_category.call_args_list == [call("All"), call("Primary"), call("Secondary"), call("Abstracts")]
    app.load_query_file.assert_not_called()
    app.verify_static_data.assert_not_called()
    assert app.method_calls[-2:] == [call.write_publication_results(), call.assert_no_failures()]
