"""Study detail safety, real mismatch handling and Excel action integration."""
from pathlib import Path
from unittest.mock import MagicMock, Mock, call

import openpyxl
import pytest

from Commons.apps.c3dc import C3DC
from Commons.apps.c3dc.study_details import StudyDetailsVerifier, validate_accession
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("value", ["phs000463/other", "phs000463'", "PHs000463", "phs1", ""])
def test_invalid_accessions_are_rejected_before_navigation(value):
    with pytest.raises(ValueError, match="Invalid dbGaP accession"):
        validate_accession(value)


def test_count_mismatch_is_reported_and_manifest_is_still_checked(tmp_path):
    app = C3DC.__new__(C3DC)
    app.page, app.results, app.failures = Mock(), [], []
    app.output_dir, app.query_file = tmp_path, Mock()
    verifier = StudyDetailsVerifier(app, "phs000463")
    verifier.verify_metadata_and_counts = lambda: verifier.record_check("Participants", 233, 234)
    verifier.verify_manifest = Mock()
    verifier.run()
    verifier.verify_manifest.assert_called_once()
    with pytest.raises(AssertionError, match="Participants"):
        app.assert_no_failures()
    assert {p.name for p in tmp_path.iterdir()} == {"StudyDetails_AllStudies.xlsx"}
    wb = openpyxl.load_workbook(tmp_path / "StudyDetails_AllStudies.xlsx", read_only=True, data_only=True)
    try:
        row = list(wb["All Checks"].values)[1]
        assert row[1:] == ("Participants", "233", "234", "FAILED")
    finally:
        wb.close()


def test_metadata_checks_only_requested_fields_and_preserves_zero_samples(tmp_path):
    app = C3DC.__new__(C3DC)
    app.page, app.results, app.failures = Mock(), [], []
    app.output_dir = tmp_path
    verifier = StudyDetailsVerifier(app, "phs000463")
    verifier.run_query = Mock(side_effect=[
        [{"accession": "phs000463", "name": "TARGET Study", "description": "Full study description"}],
        [{"participants": 233, "samples": 0, "files": 3}],
    ])
    values = {"Accession": "phs000463", "Name": "TARGET Study", "Description": "Full  study\n description",
              "Participants": "233", "Samples": "0", "Files": "3"}
    verifier.get_locator = lambda field: Mock(first=Mock(inner_text=Mock(return_value=values[field])))
    verifier.verify_metadata_and_counts()
    assert verifier.run_query.call_args_list == [call("StudyMetadata"), call("StudyCounts")]
    assert [row[1] for row in verifier.rows] == list(values)
    assert all(row[-1] == "PASSED" for row in verifier.rows)
    assert not app.failures


def test_manifest_download_saves_and_opens_completed_workbook(tmp_path, monkeypatch):
    app = C3DC.__new__(C3DC)
    app.page, app.results, app.failures = MagicMock(), [], []
    app.output_dir = tmp_path
    verifier = StudyDetailsVerifier(app, "phs000463")
    url = "https://example.org/phs000463_manifest.xlsx"
    verifier.get_expected_manifest_url = Mock(return_value=url)
    link = Mock()
    link.get_attribute.return_value = url
    verifier.get_locator = Mock(return_value=link)
    monkeypatch.setattr("Commons.apps.c3dc.study_details.expect", Mock())
    download = app.page.expect_download.return_value.__enter__.return_value.value
    download.suggested_filename = "phs000463_manifest.xlsx"
    # A real Excel fixture verifies the downloaded file is parsed, not just named.
    fixture = ROOT / "InputFiles/C3DC/C3DC_StudyDetails.xlsx"
    download.save_as.side_effect = lambda path: path.write_bytes(fixture.read_bytes())
    verifier.verify_manifest()
    link.click.assert_called_once()
    assert (tmp_path / download.suggested_filename).is_file()
    assert [row[1] for row in verifier.rows] == ["Manifest URL", "Manifest filename", "Manifest download opens"]
    assert all(row[-1] == "PASSED" for row in verifier.rows)


def test_query_binds_accession_without_substituting_cypher(tmp_path):
    app = MagicMock(output_dir=tmp_path)
    query = "MATCH (s:study {dbgap_accession:$accession}) RETURN s.study_name LIMIT 2"
    app.query_file.query_for_tab.return_value = query
    session = app.connected_source.return_value.get_bolt_driver.return_value.session.return_value.__enter__.return_value
    session.run.return_value = [{"name": "Study"}]
    verifier = StudyDetailsVerifier(app, "phs000463")
    assert verifier.run_query("StudyMetadata") == [{"name": "Study"}]
    session.run.assert_called_once_with(query, {"accession": "phs000463"})


def test_one_study_error_does_not_erase_or_suppress_other_studies(tmp_path):
    app = C3DC.__new__(C3DC)
    app.page, app.results, app.failures = Mock(), [], []
    app.output_dir, app.query_file = tmp_path, Mock()
    app.begin_study_details_report()
    broken = StudyDetailsVerifier(app, "phs000463")
    broken.verify_metadata_and_counts = Mock(side_effect=ValueError("No study metadata"))
    broken.verify_manifest = Mock()
    broken.run()
    broken.verify_manifest.assert_called_once()
    working = StudyDetailsVerifier(app, "phs000464")
    working.verify_metadata_and_counts = lambda: working.record_check("Participants", 1701, 1701)
    working.verify_manifest = Mock()
    working.run()
    assert list(app._study_details_results) == ["phs000463", "phs000464"]
    wb = openpyxl.load_workbook(tmp_path / "StudyDetails_AllStudies.xlsx", read_only=True, data_only=True)
    try:
        rows = list(wb["Summary"].values)[1:]
        assert [(r[0], r[1]) for r in rows] == [("phs000463", "FAILED"), ("phs000464", "PASSED")]
    finally:
        wb.close()
    with pytest.raises(AssertionError, match="No study metadata"):
        app.assert_no_failures()


def test_excel_uses_visible_navigation_and_reusable_accession():
    app = Mock(spec=C3DC)
    run_testcase_excel(app, ROOT / "Testcases/C3DC/study_details/TC01_C3DC_phs000463_StudyDetails.xlsx")
    assert app.method_calls[:4] == [call.load_query_file("C3DC_StudyDetails.xlsx"), call.accept_banner(), call.begin_study_details_report(), call.open_studies_listing()]
    opened = [c.args[0] for c in app.method_calls if c[0] == "open_study_details"]
    verified = [c.args[0] for c in app.method_calls if c[0] == "verify_study_details"]
    assert len(opened) == len(set(opened)) == 49
    assert opened == verified
    assert opened[0] == "phs000463" and opened[-1] == "phs004490"
    assert app.assert_no_failures.call_count == 1
    assert app.method_calls[-1] == call.assert_no_failures()
    assert app.goto.call_count == 48


def test_target_excel_runs_only_the_nine_target_studies():
    app = Mock(spec=C3DC)
    run_testcase_excel(app, ROOT / "Testcases/C3DC/study_details/TC01_C3DC_Verify_StudyDetails_Target.xlsx")
    expected = [f"phs{number:06}" for number in range(463, 472)]
    opened = [step.args[0] for step in app.method_calls if step[0] == "open_study_details"]
    verified = [step.args[0] for step in app.method_calls if step[0] == "verify_study_details"]
    assert opened == verified == expected
    app.begin_study_details_report.assert_called_once_with("StudyDetails_Target")
    app.load_query_file.assert_called_once_with("C3DC_StudyDetails.xlsx")
    assert app.goto.call_count == 8
    assert app.method_calls[-1] == call.assert_no_failures()
    app.assert_no_failures.assert_called_once()


def test_target_report_does_not_overwrite_the_all_studies_report(tmp_path):
    app = C3DC.__new__(C3DC)
    app.page, app.output_dir = None, tmp_path
    app.begin_study_details_report()
    original = StudyDetailsVerifier(app, "phs002790")
    original.rows = [["phs002790", "Participants", "9729", "9729", "PASSED"]]
    original.write_consolidated_report()
    before = (tmp_path / "StudyDetails_AllStudies.xlsx").read_bytes()
    app.begin_study_details_report("StudyDetails_Target")
    target = StudyDetailsVerifier(app, "phs000463")
    target.rows = [["phs000463", "Participants", "233", "233", "PASSED"]]
    target.write_consolidated_report()
    assert (tmp_path / "StudyDetails_AllStudies.xlsx").read_bytes() == before
    assert (tmp_path / "StudyDetails_Target.xlsx").is_file()
    assert {p.name for p in tmp_path.iterdir()} == {"StudyDetails_AllStudies.xlsx", "StudyDetails_Target.xlsx"}
    assert list(app._study_details_results) == ["phs000463"]
