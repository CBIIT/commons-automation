"""Dataset page completeness, stale-card rejection, and CI evidence."""
import json
from unittest.mock import Mock

import pytest

from Commons.apps.ins.tsv_source import _dataset_page_ready, _validate_dataset_page, read_ins_datasets_page_table

pytestmark = pytest.mark.unit


def dataset_page(start, end, total, ids):
    return {"range": f"{start}-{end} OF {total}", "start": start, "end": end,
            "total": total, "page_size": 100,
            "records": [{"id": f"#/dataset/{i}", "row": [f"Dataset {i}", f"GSE{i}", "Not Reported", ""]}
                        for i in ids]}


def reader_ui(*pages):
    ui = Mock(timeout_ms=30000)
    ui.page.url = "https://studycatalog-qa.cancer.gov/#/datasets"
    ui.page.evaluate.side_effect = list(pages)
    ui.loc.return_value.first.count.return_value = 1
    ui.loc.return_value.first.get_attribute.return_value = "bspage-link-next page-item"
    repo = Mock()
    repo.xpath.side_effect = lambda key: key
    return ui, repo


def test_reader_waits_for_the_next_range_and_identity_and_preserves_blank_counts(tmp_path):
    first = dataset_page(1, 100, 101, range(100))
    last = dataset_page(101, 101, 101, [100])
    # The counter moves to page 2 while its cards still belong to page 1.
    stale = {**first, "range": last["range"], "start": 101, "end": 101,
             "records": [first["records"][0]]}
    ui, repo = reader_ui(first, stale, last)
    path = tmp_path / "pages.json"
    table = read_ins_datasets_page_table(ui, repo, path)
    assert len(table.rows) == 101
    assert table.rows[-1] == ["Dataset 100", "GSE100", "Not Reported", ""]
    assert ui.page.evaluate.call_count == 3
    ui.page.wait_for_timeout.assert_called_once_with(100)
    assert json.loads(path.read_text())["unique_dataset_ids"] == 101


def test_duplicate_within_a_page_is_not_silently_deduplicated():
    with pytest.raises(AssertionError, match="Repeated INS dataset GSE1"):
        _validate_dataset_page(dataset_page(1, 2, 2, [1, 1]), {})


def test_duplicate_across_pages_reports_both_ranges():
    seen = {}
    _validate_dataset_page(dataset_page(1, 100, 101, range(100)), seen)
    with pytest.raises(AssertionError, match="101-101 OF 101.*1-100 OF 101"):
        _validate_dataset_page(dataset_page(101, 101, 101, [99]), seen)


def test_disabled_next_cannot_truncate_a_successful_comparison(tmp_path):
    ui, repo = reader_ui(dataset_page(1, 100, 101, range(100)))
    ui.loc.return_value.first.get_attribute.return_value = "bspage-link-next page-item disabled"
    path = tmp_path / "pages.json"
    # A serializable last snapshot is included with the failure evidence.
    ui.page.evaluate.side_effect = [dataset_page(1, 100, 101, range(100)), {"range": "1-100 OF 101"}]
    with pytest.raises(AssertionError, match="before all records were read"):
        read_ins_datasets_page_table(ui, repo, path)
    assert "Next page is unavailable" in json.loads(path.read_text())["error"]


def test_timeout_saves_last_observed_page_for_ci(tmp_path):
    ui, repo = reader_ui()
    ui.timeout_ms = 0
    ui.page.evaluate.side_effect = None
    ui.page.evaluate.return_value = dataset_page(101, 200, 8467, [])
    path = tmp_path / "pages.json"
    with pytest.raises(TimeoutError, match="did not finish"):
        read_ins_datasets_page_table(ui, repo, path)
    evidence = json.loads(path.read_text())
    assert evidence["reader"] == "atomic-pages-v1"
    assert evidence["last_observed_page"]["range"] == "101-200 OF 8467"


def test_zero_results_returns_an_empty_table():
    ui, repo = reader_ui(dataset_page(0, 0, 0, []))
    assert read_ins_datasets_page_table(ui, repo).rows == []
    ui.loc.assert_not_called()


def test_readiness_rejects_a_filter_total_that_changes_mid_run():
    page = dataset_page(101, 200, 9000, range(100, 200))
    assert not _dataset_page_ready(page, {"start": 101, "pageSize": 100, "total": 8467, "previousFirst": "#/dataset/0"})
