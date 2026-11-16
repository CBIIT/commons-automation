"""Cohort Analyzer example creation checks and Excel integration."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc import C3DC
from Commons.apps.c3dc.cohort_analyzer import (
    AnalyzerCohort, _example_cohort_checks, verify_example_cohorts_created,
)
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
CASE = Path(__file__).resolve().parents[2] / 'Testcases/C3DC/cohort_analyzer/TC01_C3DC_Verify_Add_Example_Cohorts.xlsx'
NAMES = ('Example Cohort 1', 'Example Cohort 2', 'Example Cohort 3')


def example_cohorts():
    return [AnalyzerCohort(name, count, True) for name, count in zip(NAMES, (24, 25, 30))]


def test_example_counts_can_vary_and_entries_can_be_sorted_differently():
    assert all(_example_cohort_checks(list(reversed(example_cohorts())), NAMES).values())


@pytest.mark.parametrize('problem', ['missing', 'duplicate', 'wrong_name', 'empty', 'unselected'])
def test_example_verification_rejects_incomplete_or_incorrect_entries(problem):
    cohorts = example_cohorts()
    if problem == 'missing':
        cohorts.pop()
    elif problem == 'duplicate':
        cohorts[2] = cohorts[0]
    elif problem == 'wrong_name':
        cohorts[2] = AnalyzerCohort('Other Cohort', 24, True)
    elif problem == 'empty':
        cohorts[2] = AnalyzerCohort(NAMES[2], 0, True)
    else:
        cohorts[2] = AnalyzerCohort(NAMES[2], 24, False)
    assert not all(_example_cohort_checks(cohorts, NAMES).values())


def test_example_verification_requires_creation_in_this_flow():
    app = C3DC.__new__(C3DC)
    with pytest.raises(AssertionError, match='Add example cohorts before'):
        verify_example_cohorts_created(app, '; '.join(NAMES))


def test_wrong_examples_are_recorded_as_failures(monkeypatch):
    app = C3DC.__new__(C3DC)
    app.results, app.failures, app.query_file = [], [], None
    app._example_cohorts_added = True
    cohorts = example_cohorts()
    cohorts[2] = AnalyzerCohort('Wrong Cohort', 24, True)
    monkeypatch.setattr('Commons.apps.c3dc.cohort_analyzer.read_analyzer_cohorts', lambda _: cohorts)
    monkeypatch.setattr('Commons.apps.c3dc.cohort_analyzer.expect', lambda _: Mock())
    app.page, app.repo = Mock(), Mock()
    verify_example_cohorts_created(app, '; '.join(NAMES))
    with pytest.raises(AssertionError, match='expected example names'):
        app.assert_no_failures()


def test_analyzer_excel_navigates_adds_examples_once_and_verifies_without_database():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE)
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_cohort_analyzer', 'add_example_cohorts',
        'verify_example_cohorts_created', 'assert_no_failures',
    ]
    app.add_example_cohorts.assert_called_once_with()
    app.verify_example_cohorts_created.assert_called_once_with('; '.join(NAMES))
    app.load_query_file.assert_not_called()
