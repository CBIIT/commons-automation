"""Regression checks for adding a filtered participant set to an existing cohort."""
from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc import C3DC
from Commons.apps.c3dc import cohort
from Testcases.unit.python_cases import run_python_case, case_report_name

pytestmark = pytest.mark.unit
CASE = Path(__file__).resolve().parents[2] / 'Testcases/C3DC/cohorts/test_TC10_C3DC_Verify_AddToExistingCohort_AllParticipants.py'


def addition_baseline():
    source = cohort.CohortDetails('New Cohort', 2, (('P1', 'S1'), ('P2', 'S1')), 'Original description')
    addition = cohort.CohortAddition(source, ('P2', 'P3'), ('cohort-item-New Cohort',))
    actual = replace(source, participant_count=3, participants=(('P3', 'S2'), ('P2', 'S1'), ('P1', 'S1')))
    return addition, actual


def test_addition_counts_overlapping_participants_once_and_ignores_row_order():
    addition, actual = addition_baseline()
    assert all(cohort._cohort_addition_checks(addition, actual, addition.item_ids).values())


@pytest.mark.parametrize('problem,failed_check', [
    ('wrong_id', 'complete participant IDs'),
    ('missing_original', 'complete participant IDs'),
    ('duplicate', 'unique participant rows'),
    ('simple_sum', 'participant count'),
    ('renamed', 'same cohort name'),
    ('description', 'description unchanged'),
    ('new_cohort', 'cohort list unchanged'),
])
def test_addition_rejects_incorrect_updates(problem, failed_check):
    addition, actual = addition_baseline()
    ids = addition.item_ids
    if problem == 'wrong_id':
        actual = replace(actual, participants=(('P1', 'S1'), ('P2', 'S1'), ('WRONG', 'S2')))
    elif problem == 'missing_original':
        actual = replace(actual, participant_count=2, participants=(('P2', 'S1'), ('P3', 'S2')))
    elif problem == 'duplicate':
        actual = replace(actual, participants=actual.participants + (('P1', 'S1'),))
    elif problem == 'simple_sum':
        actual = replace(actual, participant_count=4)
    elif problem == 'renamed':
        actual = replace(actual, name='Another cohort')
    elif problem == 'description':
        actual = replace(actual, description='')
    else:
        ids += ('cohort-item-Unexpected',)
    assert not cohort._cohort_addition_checks(addition, actual, ids)[failed_check]


def test_addition_requires_at_least_one_new_participant():
    addition, _ = addition_baseline()
    addition = replace(addition, incoming=tuple(p for p, _ in addition.source.participants))
    assert not cohort._cohort_addition_checks(addition, addition.source, addition.item_ids)['new participants present']


def test_addition_and_verification_require_their_baselines():
    app = C3DC.__new__(C3DC)
    with pytest.raises(AssertionError, match='Remember an existing cohort'):
        cohort.add_all_participants_to_existing_cohort(app)
    app._cohort_addition, _ = addition_baseline()
    app._cohort_addition = replace(app._cohort_addition, incoming=())
    with pytest.raises(AssertionError, match='Add participants to the existing cohort'):
        cohort.verify_participants_added_to_cohort(app)


@pytest.mark.parametrize('wrong_id', [False, True])
def test_persisted_addition_verification_records_membership_results(tmp_path, monkeypatch, wrong_id):
    addition, actual = addition_baseline()
    if wrong_id:
        actual = replace(actual, participants=(('P1', 'S1'), ('P2', 'S1'), ('WRONG', 'S2')))
    app = C3DC.__new__(C3DC)
    app._cohort_addition = addition
    app.results, app.failures, app.query_file = [], [], None
    app.page, app.ui, app.repo = Mock(), Mock(), Mock()
    app.BANNER_KEYS, app.output_dir = [], tmp_path
    dialog = Mock()
    dialog.locator.return_value.evaluate_all.return_value = list(addition.item_ids)
    monkeypatch.setattr(cohort, 'close_cohorts', lambda _: None)
    monkeypatch.setattr(cohort, 'open_cohorts', lambda _: dialog)
    monkeypatch.setattr(cohort, 'select_cohort', lambda *_: None)
    monkeypatch.setattr(cohort, 'read_selected_cohort', lambda _: actual)
    cohort.verify_participants_added_to_cohort(app)
    app.page.reload.assert_called_once_with(wait_until='domcontentloaded')
    evidence = json.loads((tmp_path / 'cohort_addition.verification.json').read_text())
    assert evidence['expected_unique_participant_count'] == 3
    if wrong_id:
        assert evidence['missing_ids'] == ['P3']
        with pytest.raises(AssertionError, match='complete participant IDs'):
            app.assert_no_failures()
    else:
        assert all(evidence['checks_after_reload'].values())
        app.assert_no_failures()


def test_addition_excel_reuses_creation_then_replaces_filter_and_adds_all():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_python_case(app, CASE)
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter',
        'create_cohort_from_all_participants', 'verify_cohort_created',
        'remember_cohort_for_addition', 'close_cohorts', 'replace_cohort_filter',
        'add_all_participants_to_existing_cohort', 'verify_participants_added_to_cohort', 'assert_no_failures',
    ]
    app.replace_cohort_filter.assert_called_once_with('Diagnosis/Diagnosis', 'AbdominalFibromatosis', 'Adenocarcinoma')
    app.verify_participants_added_to_cohort.assert_called_once_with(case_report_name(CASE))
    app.load_query_file.assert_not_called()


def test_selected_addition_uses_only_the_checked_page_and_selected_menu_option(monkeypatch):
    app = Mock()
    app._cohort_addition, _ = addition_baseline()
    page_two = ('P3', 'P4')
    app._cohort_selected_pages = {2: page_two}
    app.ui.visible.return_value.locator.return_value.all.return_value = [Mock(), Mock()]
    monkeypatch.setattr(cohort, 'expect', lambda _: Mock())
    monkeypatch.setattr(cohort, '_visible_participant_rows', lambda _: page_two)
    filtered_reader = Mock(side_effect=AssertionError('Selected mode must not read all filtered participants'))
    monkeypatch.setattr(cohort, 'read_filtered_participants', filtered_reader)
    add = Mock()
    monkeypatch.setattr(cohort, '_add_participants_to_existing_cohort', add)
    cohort.add_selected_participants_to_existing_cohort(app)
    add.assert_called_once_with(app, page_two, 'Cohort/AddSelectedParticipants')
    filtered_reader.assert_not_called()


def test_selected_addition_rejects_a_stale_page_snapshot(monkeypatch):
    app = Mock()
    app._cohort_addition, _ = addition_baseline()
    app._cohort_selected_pages = {2: ('P3',)}
    monkeypatch.setattr(cohort, '_visible_participant_rows', lambda _: ('WRONG',))
    add = Mock()
    monkeypatch.setattr(cohort, '_add_participants_to_existing_cohort', add)
    with pytest.raises(AssertionError, match='Current participant rows differ'):
        cohort.add_selected_participants_to_existing_cohort(app)
    add.assert_not_called()


def test_selected_addition_rejects_multiple_remembered_pages():
    app = C3DC.__new__(C3DC)
    app._cohort_addition, _ = addition_baseline()
    app._cohort_selected_pages = {1: ('P1',), 2: ('P3',)}
    with pytest.raises(AssertionError, match='Select only the participant page'):
        cohort.add_selected_participants_to_existing_cohort(app)


def test_replacing_page_selection_rejects_stale_current_page_before_clearing(monkeypatch):
    app = Mock()
    app._cohort_selected_pages = {1: ('P1',)}
    monkeypatch.setattr(cohort, '_visible_participant_rows', lambda _: ('OTHER',))
    with pytest.raises(AssertionError, match='Current participant page differs'):
        cohort.select_next_participant_page_only(app)
    app.ui.visible.return_value.locator.assert_not_called()


def test_selected_addition_excel_creates_from_page_one_then_replaces_selection():
    path = CASE.with_name('test_TC11_C3DC_Verify_AddToExistingCohort_SelectedParticipants.py')
    app = Mock(NAME='C3DC', spec=C3DC)
    run_python_case(app, path)
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_participant_page',
        'create_cohort_from_selected_participants', 'verify_cohort_created',
        'remember_cohort_for_addition', 'close_cohorts', 'select_next_participant_page_only',
        'add_selected_participants_to_existing_cohort', 'verify_participants_added_to_cohort', 'assert_no_failures',
    ]
    app.select_participant_page.assert_called_once_with(1)
    app.add_all_participants_to_existing_cohort.assert_not_called()
    app.select_filter.assert_not_called()
    app.load_query_file.assert_not_called()
