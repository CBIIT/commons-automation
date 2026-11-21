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


def test_exclusive_regions_partition_the_union_without_double_counting():
    from Commons.apps.c3dc.cohort_analyzer import exclusive_regions
    sets = [{'a', 'ab', 'ac', 'abc'}, {'b', 'ab', 'bc', 'abc'}, {'c', 'ac', 'bc', 'abc'}]
    actual = exclusive_regions(sets)
    assert actual == {1: {'a'}, 2: {'b'}, 3: {'ab'}, 4: {'c'}, 5: {'ac'}, 6: {'bc'}, 7: {'abc'}}
    assert set().union(*actual.values()) == set().union(*sets)
    assert sum(map(len, actual.values())) == len(set().union(*sets))


def test_histogram_counts_distinct_participants_not_repeated_visits():
    from Commons.apps.c3dc.cohort_analyzer import _metadata_chart_counts
    records = {
        ('P1', 'S1'): {'race': ['R1', 'R2'], 'treatment_responses': [{'response': ['Complete']}, {'response': ['Complete']}]},
        ('P2', 'S1'): {'race': ['R1'], 'treatment_responses': [{'response': ['Complete', 'Progressive']}]},
    }
    assert _metadata_chart_counts(records, 'race') == {'R1': 2, 'R2': 1}
    assert _metadata_chart_counts(records, 'response') == {'Complete': 2, 'Progressive': 1}
    with pytest.raises(ValueError, match='Unsupported histogram'):
        _metadata_chart_counts(records, 'unsupported')


def test_metadata_export_membership_retains_study_identity():
    from Commons.apps.c3dc.cohort_analyzer import _export_participant_pairs
    data = {'Cohort': [{'dbgap_accession': 'S1', 'consent_groups': [{'participants': [{'participant_id': 'P1'}]}]},
                       {'dbgap_accession': 'S2', 'consent_groups': [{'participants': [{'participant_id': 'P1'}]}]}]}
    assert _export_participant_pairs(data) == {('P1', 'S1'), ('P1', 'S2')}
    with pytest.raises(AssertionError, match='no study context'):
        _export_participant_pairs({'participant_id': 'P1'})


def test_survival_observations_ignore_missing_ages_and_use_latest_follow_up():
    from Commons.apps.c3dc.cohort_analyzer import _survival_observations
    records = {
        ('P1', 'S1'): {'diagnoses': [{'age_at_diagnosis': -999}, {'age_at_diagnosis': 100}],
                        'survivals': [{'age_at_last_known_survival_status': 150, 'last_known_survival_status': 'Alive'},
                                      {'age_at_last_known_survival_status': 300, 'last_known_survival_status': 'Dead'}]},
        ('P2', 'S1'): {'diagnoses': [{'age_at_diagnosis': -999}],
                        'survivals': [{'age_at_last_known_survival_status': 300, 'last_known_survival_status': 'Alive'}]},
    }
    assert _survival_observations(records) == [(200, True)]


@pytest.mark.parametrize('path', sorted(CASE.parent.glob('TC*.xlsx')), ids=lambda p: p.stem)
def test_analyzer_workbooks_have_valid_actions_and_reusable_dispatch(path):
    import openpyxl
    from Commons.excel_testcase.registry import get_profile
    profile = get_profile('C3DC')
    workbook = openpyxl.load_workbook(path)
    sheet = workbook['Steps']
    assert sheet.sheet_view.showGridLines is not False
    actions = [row[1] for row in list(sheet.values)[2:] if row[1]]
    assert actions[-1] == 'assert_no_failures'
    assert len(sheet.data_validations.dataValidation) > 0
    assert all(action in profile.excel_actions for action in actions)
    workbook.close()
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, path)
    app.assert_no_failures.assert_called_once()
    app.load_query_file.assert_not_called()


def test_analyzer_readiness_ignores_null_and_unrelated_participant_responses(monkeypatch):
    from Commons.apps.c3dc.cohort_analyzer import _wait_for_analyzer_participants
    app = Mock()
    app.ui.timeout_ms = 100
    valid, empty, other = Mock(), Mock(), Mock()
    valid.json.return_value = {'data': {'participantOverview': [{'participant_id': 'P1', 'study_id': 'S1'}]}}
    empty.json.return_value = {'data': {'participantOverview': None}}
    other.json.return_value = {'data': {'participantOverview': [{'participant_id': 'P2', 'study_id': 'S1'}]}}
    app._analyzer_responses = [valid, other, empty]
    monkeypatch.setattr('Commons.apps.c3dc.cohort_analyzer._expected_members', lambda _: {('P1', 'S1')})
    _wait_for_analyzer_participants(app)
    for response in (valid, empty, other):
        response.finished.assert_called_once()


def test_analyzer_readiness_rejects_a_response_for_another_cohort(monkeypatch):
    from Commons.apps.c3dc.cohort_analyzer import _wait_for_analyzer_participants
    app = Mock()
    app.ui.timeout_ms = 1
    response = Mock()
    response.json.return_value = {'data': {'participantOverview': [{'participant_id': 'P2', 'study_id': 'S1'}]}}
    app._analyzer_responses = [response]
    monkeypatch.setattr('Commons.apps.c3dc.cohort_analyzer._expected_members', lambda _: {('P1', 'S1')})
    with pytest.raises(AssertionError, match='lookup did not finish'):
        _wait_for_analyzer_participants(app)
    app.page.evaluate.assert_not_called()


def test_chart_readiness_waits_for_the_requested_aggregation():
    from Commons.apps.c3dc.cohort_analyzer import _wait_for_analyzer_charts
    app = Mock()
    app.ui.timeout_ms = 100
    count, percentage = Mock(), Mock()
    count.request.post_data_json = {'variables': {'charts': [{'property': 'race', 'type': 'count'}]}}
    percentage.request.post_data_json = {'variables': {'charts': [{'property': 'race', 'type': 'percentage'}]}}
    app._analyzer_chart_responses = [count, percentage]
    _wait_for_analyzer_charts(app, {'race': 'count'})
    count.finished.assert_called_once()
    percentage.finished.assert_not_called()


def test_chart_readiness_rejects_an_old_aggregation():
    from Commons.apps.c3dc.cohort_analyzer import _wait_for_analyzer_charts
    app = Mock()
    app.ui.timeout_ms = 1
    response = Mock()
    response.request.post_data_json = {'variables': {'charts': [{'property': 'race', 'type': 'percentage'}]}}
    app._analyzer_chart_responses = [response]
    with pytest.raises(AssertionError, match='Chart response did not finish'):
        _wait_for_analyzer_charts(app, {'race': 'count'})
    response.finished.assert_not_called()
