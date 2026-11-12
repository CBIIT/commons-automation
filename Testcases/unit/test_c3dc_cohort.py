"""Cohort membership regressions and the Excel testcase integration."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc import C3DC
from Commons.apps.c3dc.cohort import CohortCreation, CohortDetails, verify_cohort_created
from Commons.excel_testcase.registry import get_profile
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "Testcases/C3DC/cohorts/TC01_C3DC_CreateCohort_phs002790_Race-AmericanIndianAlaskaNative.xlsx"


def cohort_app():
    app = C3DC.__new__(C3DC)
    app.results, app.failures = [], []
    app.query_file = None
    app._cohort_creation = CohortCreation(3, (("P1", "phs002790"), ("P2", "phs002790")))
    return app


def test_same_count_with_wrong_participants_fails(monkeypatch):
    """A popup count alone must not pass a cohort built from the wrong selection."""
    app = cohort_app()
    details = CohortDetails("New Cohort", 2, (("P1", "phs002790"), ("WRONG", "phs002790")))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    with pytest.raises(AssertionError, match="participant and study IDs"):
        app.assert_no_failures()


def test_duplicate_participants_fail_even_when_all_expected_ids_are_present(monkeypatch):
    app = cohort_app()
    details = CohortDetails("New Cohort", 2, app._cohort_creation.participants + (("P1", "phs002790"),))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    with pytest.raises(AssertionError, match="unique participant rows"):
        app.assert_no_failures()


def test_wrong_study_for_a_correct_participant_id_fails(monkeypatch):
    app = cohort_app()
    details = CohortDetails("New Cohort", 2, (("P1", "phs000463"), ("P2", "phs002790")))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    assert any("participant and study IDs" in failure for failure in app.failures)


def test_complete_cohort_passes_regardless_of_row_sort_order(monkeypatch):
    app = cohort_app()
    details = CohortDetails("New Cohort 2", 2, tuple(reversed(app._cohort_creation.participants)))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    assert verify_cohort_created(app) == details
    app.assert_no_failures()


def test_verification_requires_a_creation_baseline():
    app = C3DC.__new__(C3DC)
    with pytest.raises(AssertionError, match="Create a cohort before"):
        verify_cohort_created(app)


def test_excel_cohort_case_runs_the_requested_workflow_without_a_database():
    app = Mock(NAME="C3DC", spec=C3DC)
    run_testcase_excel(app, CASE)
    assert [c[0] for c in app.method_calls] == [
        "accept_banner", "open_explore", "select_filter", "select_filter",
        "create_cohort_from_all_participants", "verify_cohort_created", "assert_no_failures",
    ]
    assert app.select_filter.call_args_list[0].args == ("Study/dbGaP_Accession", "phs002790")
    assert app.select_filter.call_args_list[1].args == ("Demographics/Race", "American Indian or Alaska Native")
    app.load_query_file.assert_not_called()
    assert "cohorts" in get_profile("C3DC").case_subdirs
