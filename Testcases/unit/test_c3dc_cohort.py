"""Cohort membership regressions and the Excel testcase integration."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc import C3DC
from Commons.apps.c3dc.cohort import (
    CohortCreation, CohortDetails, CohortDuplication, CohortEdit,
    verify_cohort_created, verify_duplicate_cohort_created,
)
from Commons.excel_testcase.registry import get_profile
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]
PARTICIPANTS = (("P1", "phs002790"), ("P2", "phs002790"))
CASE = ROOT / "Testcases/C3DC/cohorts/TC01_C3DC_Verify_Create_NewCohort_AllParticipants.xlsx"


def cohort_app():
    app = C3DC.__new__(C3DC)
    app.results, app.failures = [], []
    app.query_file = None
    app._cohort_creation = CohortCreation(3, 2, "phs002790", ("P1", "P2"))
    return app


def test_participant_reader_returns_full_ids_without_study_values():
    from Commons.apps.c3dc.cohort import _visible_participant_rows

    container = Mock()
    container.evaluate.return_value = ['P001', 'P002']

    assert _visible_participant_rows(container) == ('P001', 'P002')


def test_participant_readiness_matches_filters_not_pagination():
    from Commons.apps.c3dc.cohort import _participant_filters

    requested = _participant_filters({'dbgap_accession': ['phs002790']})
    assert _participant_filters({'participant_ids': [], 'offset': 0, 'first': 50}) != requested
    assert _participant_filters({'dbgap_accession': ['phs002790'], 'offset': 50,
                                 'order_by': 'participant_id', 'sort_direction': 'asc'}) == requested
    assert _participant_filters({'dbgap_accession': ['phs000463']}) != requested


def test_all_selected_ids_are_verified_without_a_study_filter(monkeypatch):
    app = cohort_app()
    app._cohort_creation = CohortCreation(0, 2, None, ('P1', 'P2'))
    details = CohortDetails('New Cohort', 2, (('P2', 'any-study'), ('P1', 'another-study')))
    monkeypatch.setattr('Commons.apps.c3dc.cohort.read_selected_cohort', lambda _: details)

    verify_cohort_created(app)

    app.assert_no_failures()


@pytest.mark.parametrize('ids,message', [
    ([], 'No participant IDs'),
    (['P001', ''], 'No participant IDs'),
    (['P001', 'P001'], 'Duplicate participants'),
])
def test_participant_reader_rejects_empty_or_duplicate_ids(ids, message):
    from Commons.apps.c3dc.cohort import _visible_participant_rows

    container = Mock()
    container.evaluate.return_value = ids
    with pytest.raises(AssertionError, match=message):
        _visible_participant_rows(container)


def test_same_count_with_wrong_participants_fails(monkeypatch):
    """A popup count alone must not pass a cohort built from the wrong selection."""
    app = cohort_app()
    details = CohortDetails("New Cohort", 2, (("P1", "phs002790"), ("WRONG", "phs002790")))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    with pytest.raises(AssertionError, match="participant IDs"):
        app.assert_no_failures()


def test_duplicate_participants_fail_even_when_all_expected_ids_are_present(monkeypatch):
    app = cohort_app()
    details = CohortDetails("New Cohort", 2, PARTICIPANTS + (("P1", "phs002790"),))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    with pytest.raises(AssertionError, match="unique participant rows"):
        app.assert_no_failures()


def test_wrong_study_for_a_correct_participant_id_fails(monkeypatch):
    app = cohort_app()
    details = CohortDetails("New Cohort", 2, (("P1", "phs000463"), ("P2", "phs002790")))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    assert any("selected study IDs" in failure for failure in app.failures)


def test_complete_cohort_passes_regardless_of_row_sort_order(monkeypatch):
    app = cohort_app()
    details = CohortDetails("New Cohort 2", 2, tuple(reversed(PARTICIPANTS)))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    assert verify_cohort_created(app) == details
    app.assert_no_failures()


def test_verification_requires_a_creation_baseline():
    app = C3DC.__new__(C3DC)
    with pytest.raises(AssertionError, match="Create a cohort before"):
        verify_cohort_created(app)


def test_all_participants_creation_does_not_read_or_paginate_results(monkeypatch):
    from Commons.apps.c3dc import cohort
    app = Mock()
    app.repo.xpath.side_effect = lambda key: key
    app.ui.stable_text.return_value = "86"
    app.ui.visible.return_value.inner_text.return_value = "VIEW ALL COHORTS(3)"
    app._active_study_accession = "phs002790"
    read_results = Mock(side_effect=AssertionError("All-participant creation must not read the table"))
    monkeypatch.setattr(cohort, "read_filtered_participants", read_results)
    monkeypatch.setattr(cohort, "cohort_dialog", lambda _: Mock())
    monkeypatch.setattr(cohort, "expect", lambda _: Mock())
    cohort.create_cohort_from_all_participants(app)
    read_results.assert_not_called()
    app.open_tab.assert_not_called()
    app._wait_explore_results_ready.assert_not_called()
    assert [c.args[0] for c in app.ui.click.call_args_list] == ["Cohort/CreateNew", "Cohort/AllParticipants"]
    assert app._cohort_creation == CohortCreation(3, 86, "phs002790")


@pytest.mark.parametrize("details, failure", [
    (CohortDetails("New Cohort", 1, (("P1", "phs002790"),)), "participant count"),
    (CohortDetails("New Cohort", 2, (("P1", "phs002790"), ("P1", "phs002790"))), "unique participant rows"),
    (CohortDetails("New Cohort", 2, (("P1", "phs000463"), ("P2", "phs002790"))), "selected study IDs"),
])
def test_count_baseline_still_rejects_invalid_cohort(monkeypatch, details, failure):
    app = cohort_app()
    app._cohort_creation = CohortCreation(3, 2, "phs002790")
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    assert any(failure in message for message in app.failures)


def test_count_baseline_accepts_complete_cohort(monkeypatch):
    app = cohort_app()
    app._cohort_creation = CohortCreation(3, 2, "phs002790")
    details = CohortDetails("New Cohort", 2, (("P1", "phs002790"), ("P2", "phs002790")))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", lambda _: details)
    verify_cohort_created(app)
    app.assert_no_failures()


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


def test_removal_message_failure_still_cancels_and_never_confirms(monkeypatch):
    """A changed warning must fail without leaving a destructive prompt open."""
    from Commons.apps.c3dc import cohort
    app = Mock()
    app.results = []
    dialog, confirmation, cancel, confirm, message = (Mock() for _ in range(5))
    app.repo.xpath.side_effect = lambda key: key
    app.page.locator.return_value = confirmation
    fields = {'xpath=Cohort/CancelRemoval': cancel,
              'xpath=Cohort/ConfirmRemoval': confirm,
              'xpath=Cohort/RemovalMessage': message}
    confirmation.locator.side_effect = fields.__getitem__
    assertions = Mock()
    assertions.to_have_text.side_effect = AssertionError('Warning text changed')
    monkeypatch.setattr(cohort, 'expect', lambda _: assertions)
    monkeypatch.setattr(cohort, 'cohort_dialog', lambda _: dialog)
    monkeypatch.setattr(cohort, 'read_selected_cohort', lambda _: CohortDetails('New Cohort', 0, ()))
    with pytest.raises(AssertionError, match='Warning text changed'):
        cohort.verify_cohort_removal_confirmation(app, 'table', 'Expected full warning')
    cancel.click.assert_called_once()
    confirm.click.assert_not_called()
    assert app.results == []


def test_removal_excel_checks_all_three_controls_without_database():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC06_C3DC_Verify_Cohort_Removal_Confirmation.xlsx'))
    app.duplicate_cohort_repeatedly.assert_called_once_with(3)
    calls = app.verify_cohort_removal_confirmation.call_args_list
    assert [call.args[0] for call in calls] == ['table', 'cohort', 'all']
    assert calls[0].args[1] == calls[1].args[1]
    assert 'delete this cohort?' in calls[0].args[1]
    assert 'delete all cohorts?' in calls[2].args[1]
    app.load_query_file.assert_not_called()


@pytest.mark.parametrize('target', ['table', 'cohort', 'all'])
def test_confirmed_removal_rejects_wrong_remaining_cohorts(monkeypatch, target):
    """A lower count must not pass if Confirm removed the wrong cohort."""
    from Commons.apps.c3dc import cohort
    app, dialog, items, confirmation = (Mock() for _ in range(4))
    app.results = []
    app.repo.xpath.side_effect = lambda key: key
    app.page.locator.return_value = confirmation
    dialog.locator.return_value = items
    items.get_attribute.return_value = 'cohort-item-selected'
    items.evaluate_all.side_effect = [
        ['cohort-item-selected', 'cohort-item-other'],
        ['cohort-item-selected', 'cohort-item-other'],  # Cancel preserves both.
        ['cohort-item-selected'],  # Confirm incorrectly left the deleted target.
    ]
    monkeypatch.setattr(cohort, 'expect', lambda _: Mock())
    monkeypatch.setattr(cohort, 'cohort_dialog', lambda _: dialog)
    monkeypatch.setattr(cohort, 'read_selected_cohort', lambda _: CohortDetails('Selected', 0, ()))
    with pytest.raises(AssertionError, match='Confirm removed the wrong cohort'):
        cohort.verify_cohort_removal_confirmation(app, target, 'Expected warning')
    assert app.results == []


def test_manifest_diagnosis_rows_do_not_inflate_participant_count(tmp_path):
    from Commons.apps.c3dc.cohort import _read_manifest_participants, _cohort_manifest_checks
    path = tmp_path / 'manifest.csv'
    path.write_text('\ufeffParticipant ID,Study ID,Diagnosis\nP1,phs002790,"Diagnosis, NOS"\nP1,phs002790,Other diagnosis\nP2,phs002790,Diagnosis\n', encoding='utf-8')
    source = CohortDetails('Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")))
    rows = _read_manifest_participants(path)
    assert len(rows) == 3
    assert all(_cohort_manifest_checks(source, rows).values())


@pytest.mark.parametrize('rows', [
    [('P1', 'phs002790'), ('WRONG', 'phs002790')],
    [('P1', 'phs002790'), ('P2', 'phs000463')],
    [('P1', 'phs002790'), ('P1', 'phs002790')],
    [('P1', 'phs002790'), ('P2', 'phs002790'), ('P3', 'phs002790')],
])
def test_manifest_rejects_missing_extra_or_wrong_study_participants(rows):
    from Commons.apps.c3dc.cohort import _cohort_manifest_checks
    source = CohortDetails('Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")))
    assert not all(_cohort_manifest_checks(source, rows).values())


@pytest.mark.parametrize('content', [
    'Participant ID,Wrong Column\nP1,phs002790\n',
    'Participant ID,Study ID\n',
    'Participant ID,Study ID\n,phs002790\n',
    'Participant ID,Study ID\nP1,\n',
    'Participant ID,Study ID\nP1,phs002790,Extra\n',
])
def test_manifest_rejects_empty_or_malformed_id_data(tmp_path, content):
    from Commons.apps.c3dc.cohort import _read_manifest_participants
    path = tmp_path / 'manifest.csv'
    path.write_text(content)
    with pytest.raises(AssertionError):
        _read_manifest_participants(path)


def test_manifest_excel_downloads_then_verifies_without_database():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC07_C3DC_Verify_Cohort_ManifestCsv_Download.xlsx'))
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter', 'select_filter',
        'create_cohort_from_all_participants', 'verify_cohort_created',
        'download_cohort_manifest', 'verify_cohort_manifest', 'assert_no_failures',
    ]
    app.download_cohort_manifest.assert_called_once_with('TC07_C3DC_Verify_Cohort_ManifestCsv_Download.xlsx')
    app.load_query_file.assert_not_called()


def metadata_fixture():
    return {'New Cohort': [{
        'study_id': 'phs002790', 'dbgap_accession': 'phs002790', 'guid': 'study-guid',
        'consent_groups': [{'guid': 'consent-guid', 'participants': [
            {'participant_id': participant_id, 'study_guid': 'study-guid', 'consent_group_guid': 'consent-guid'}
            for participant_id in ('P1', 'P2')
        ]}],
    }]}


def test_metadata_resolves_ids_from_the_study_consent_hierarchy():
    from Commons.apps.c3dc.cohort import _metadata_participant_pairs
    rows, studies = _metadata_participant_pairs(metadata_fixture(), 'New Cohort')
    assert rows == [('P1', 'phs002790'), ('P2', 'phs002790')]
    assert studies == {'phs002790'}


@pytest.mark.parametrize('field,value', [
    ('participant_id', ''),
    ('study_guid', 'wrong-study-guid'),
    ('consent_group_guid', 'wrong-consent-guid'),
])
def test_metadata_rejects_missing_ids_or_incorrect_parent_links(field, value):
    from Commons.apps.c3dc.cohort import _metadata_participant_pairs
    data = metadata_fixture()
    data['New Cohort'][0]['consent_groups'][0]['participants'][0][field] = value
    with pytest.raises(AssertionError):
        _metadata_participant_pairs(data, 'New Cohort')


def test_metadata_rejects_wrong_or_additional_cohort_names():
    from Commons.apps.c3dc.cohort import _metadata_participant_pairs
    data = metadata_fixture()
    with pytest.raises(AssertionError, match='selected cohort name'):
        _metadata_participant_pairs(data, 'Other cohort')
    data['Other cohort'] = data['New Cohort']
    with pytest.raises(AssertionError, match='selected cohort name'):
        _metadata_participant_pairs(data, 'New Cohort')


@pytest.mark.parametrize('problem', ['missing_group', 'empty_participants', 'inconsistent_study', 'duplicate_study'])
def test_metadata_rejects_incomplete_or_ambiguous_hierarchy(problem):
    from Commons.apps.c3dc.cohort import _metadata_participant_pairs
    data = metadata_fixture()
    study = data['New Cohort'][0]
    if problem == 'missing_group':
        del study['consent_groups']
    elif problem == 'empty_participants':
        study['consent_groups'][0]['participants'] = []
    elif problem == 'inconsistent_study':
        study['dbgap_accession'] = 'phs000463'
    else:
        data['New Cohort'].append(study)
    with pytest.raises(AssertionError):
        _metadata_participant_pairs(data, 'New Cohort')


@pytest.mark.parametrize('problem', [None, 'wrong_participant', 'duplicate_participant', 'extra_empty_study'])
def test_saved_metadata_verification_records_real_membership_failures(tmp_path, problem):
    import json
    from Commons.apps.c3dc.cohort import CohortMetadata, verify_cohort_metadata
    data = metadata_fixture()
    study = data['New Cohort'][0]
    participants = study['consent_groups'][0]['participants']
    if problem == 'wrong_participant':
        participants[1]['participant_id'] = 'WRONG'
    elif problem == 'duplicate_participant':
        participants.append(participants[0].copy())
    elif problem == 'extra_empty_study':
        data['New Cohort'].append({'study_id': 'phs000463', 'dbgap_accession': 'phs000463', 'guid': 'extra-study', 'consent_groups': []})
    path = tmp_path / 'metadata.json'
    path.write_text(json.dumps(data))
    app = cohort_app()
    app._cohort_metadata = CohortMetadata(CohortDetails('New Cohort', 2, PARTICIPANTS), path)
    verify_cohort_metadata(app)
    evidence = json.loads(path.with_suffix('.verification.json').read_text())
    if problem is None:
        app.assert_no_failures()
        assert all(evidence['checks'].values())
    else:
        assert not all(evidence['checks'].values())
        with pytest.raises(AssertionError, match='Cohort metadata'):
            app.assert_no_failures()


def test_metadata_excel_downloads_then_verifies_without_database():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC08_C3DC_Verify_Cohort_MetadataJson_Download.xlsx'))
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter', 'select_filter',
        'create_cohort_from_all_participants', 'verify_cohort_created',
        'download_cohort_metadata', 'verify_cohort_metadata', 'assert_no_failures',
    ]
    app.download_cohort_metadata.assert_called_once_with('TC08_C3DC_Verify_Cohort_MetadataJson_Download.xlsx')
    app.load_query_file.assert_not_called()


@pytest.mark.parametrize('control,assertion', [
    ('DeleteAll', 'to_have_text'),
    ('CreateNewHelp', 'to_have_text'),
])
def test_tooltip_copy_mismatch_cannot_be_reported_as_passing(monkeypatch, control, assertion):
    from Commons.apps.c3dc import cohort
    app, assertions = Mock(), Mock()
    app.results = []
    app.repo.xpath.side_effect = lambda key: key
    getattr(assertions, assertion).side_effect = AssertionError('Tooltip copy changed')
    monkeypatch.setattr(cohort, 'expect', lambda _: assertions)
    with pytest.raises(AssertionError, match='Tooltip copy changed'):
        cohort.verify_cohort_tooltip(app, control, 'Expected tooltip')
    assert app.results == []


def test_tooltip_excel_covers_six_controls_without_mutating_cohorts():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC09_C3DC_Verify_Cohort_Control_Tooltips.xlsx'))
    calls = app.verify_cohort_tooltip.call_args_list
    assert [call.args[0] for call in calls] == [
        'CreateNewHelp', 'AddExistingHelp', 'ViewAllHelp',
        'DeleteAll', 'DeleteSelected', 'DuplicateSelected',
    ]
    assert all(call.args[1].strip() for call in calls)
    assert all('4000 participants' in call.args[1] for call in calls[:2])
    app.verify_cohort_removal_confirmation.assert_not_called()
    app.duplicate_selected_cohort.assert_not_called()
    app.load_query_file.assert_not_called()
    assert "cohorts" in get_profile("C3DC").case_subdirs


def duplicate_app(monkeypatch, copy=None, original=None, ids=None):
    """Build a source/copy baseline so count-only false positives are exercised."""
    app = cohort_app()
    source = CohortDetails("New Cohort", 2, (("P1", "phs002790"), ("P2", "phs002790")))
    copy = copy or CohortDetails("New Cohort (Copy)", 2, tuple(reversed(source.participants)))
    app._cohort_duplication = CohortDuplication(source, ("cohort-item-New Cohort",))
    app.repo = Mock()
    app.repo.xpath.side_effect = lambda key: key
    dialog = Mock()
    items, selected = Mock(), Mock()
    items.evaluate_all.return_value = ids or ["cohort-item-New Cohort", "cohort-item-New Cohort (Copy)"]
    selected.get_attribute.return_value = "cohort-item-New Cohort (Copy)"
    dialog.locator.side_effect = lambda key: items if key == 'xpath=Cohort/Items' else selected
    monkeypatch.setattr("Commons.apps.c3dc.cohort.cohort_dialog", lambda _: dialog)
    monkeypatch.setattr("Commons.apps.c3dc.cohort.read_selected_cohort", Mock(side_effect=[copy, original or source]))
    monkeypatch.setattr("Commons.apps.c3dc.cohort.select_cohort", Mock())
    return app


def test_duplicate_preserves_all_members_regardless_of_sort_order(monkeypatch):
    app = duplicate_app(monkeypatch)
    assert verify_duplicate_cohort_created(app).name == "New Cohort (Copy)"
    app.assert_no_failures()


@pytest.mark.parametrize('copy,failure', [
    (CohortDetails('New Cohort (Copy)', 2, (("P1", "phs002790"), ("WRONG", "phs002790"))), 'participant and study IDs'),
    (CohortDetails('New Cohort (Copy)', 2, (("P1", "phs000463"), ("P2", "phs002790"))), 'participant and study IDs'),
    (CohortDetails('New Cohort (Copy)', 2, (("P1", "phs002790"), ("P1", "phs002790"))), 'unique participant rows'),
    (CohortDetails('New Cohort (Copy)', 1, (("P1", "phs002790"),)), 'participant count'),
    (CohortDetails('Unrelated cohort', 2, (("P1", "phs002790"), ("P2", "phs002790"))), 'copy name'),
    (CohortDetails('New Cohort (Copy)', 2, (("P1", "phs002790"), ("P2", "phs002790")), 'changed'), 'description'),
])
def test_duplicate_rejects_corrupt_copy(monkeypatch, copy, failure):
    app = duplicate_app(monkeypatch, copy=copy)
    verify_duplicate_cohort_created(app)
    assert any(failure in message for message in app.failures)


def test_duplicate_must_not_change_source(monkeypatch):
    altered = CohortDetails('New Cohort', 2, (("P1", "phs002790"), ("WRONG", "phs002790")))
    app = duplicate_app(monkeypatch, original=altered)
    verify_duplicate_cohort_created(app)
    assert any('source unchanged' in message for message in app.failures)


def test_duplicate_must_retain_existing_cohorts(monkeypatch):
    app = duplicate_app(monkeypatch, ids=['cohort-item-New Cohort (Copy)'])
    verify_duplicate_cohort_created(app)
    assert any('existing cohorts retained' in message for message in app.failures)


def test_duplicate_requires_baseline():
    app = C3DC.__new__(C3DC)
    with pytest.raises(AssertionError, match='Duplicate a cohort before'):
        verify_duplicate_cohort_created(app)


def test_duplicate_excel_case_is_independent_and_does_not_load_database():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC03_C3DC_Verify_Duplicate_Cohort_Creation.xlsx'))
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter', 'select_filter',
        'create_cohort_from_all_participants', 'verify_cohort_created',
        'close_cohorts', 'open_cohorts', 'duplicate_selected_cohort',
        'verify_duplicate_cohort_created', 'assert_no_failures',
    ]
    app.load_query_file.assert_not_called()


def test_selected_creation_keeps_ids_from_both_pages(monkeypatch):
    from Commons.apps.c3dc import cohort
    app = cohort_app()
    page_one = ("P1", "P2")
    page_two = ("P3", "P4")
    app._cohort_selected_pages = {1: page_one, 2: page_two}
    create = Mock()
    monkeypatch.setattr(cohort, '_create_cohort', create)
    cohort.create_cohort_from_selected_participants(app)
    create.assert_called_once_with(app, 'Cohort/SelectedParticipants', 4, page_one + page_two)


@pytest.mark.parametrize('pages,message', [
    ({}, 'Select participant pages'),
    ({1: ("P1",), 2: ("P1",)}, 'overlapping participant IDs'),
])
def test_selected_creation_rejects_empty_or_overlapping_pages(monkeypatch, pages, message):
    from Commons.apps.c3dc import cohort
    app = cohort_app()
    app._cohort_selected_pages = pages
    create = Mock()
    monkeypatch.setattr(cohort, '_create_cohort', create)
    with pytest.raises(AssertionError, match=message):
        cohort.create_cohort_from_selected_participants(app)
    create.assert_not_called()
    assert app._cohort_creation is None


@pytest.mark.parametrize('state,actual', [('disabled', True), ('enabled', False)])
def test_selected_option_must_have_requested_state(monkeypatch, state, actual):
    from Commons.apps.c3dc import cohort
    app = Mock()
    app.repo.xpath.side_effect = lambda key: key
    monkeypatch.setattr(cohort, '_selected_option_is_enabled', lambda _: actual)
    with pytest.raises(AssertionError, match=f'should be {state}'):
        cohort.verify_selected_participants_option(app, state)


@pytest.mark.parametrize('state,enabled', [('disabled', False), ('enabled', True)])
def test_option_check_dismisses_menu_without_toggling_create_or_touching_table(monkeypatch, state, enabled):
    from Commons.apps.c3dc import cohort
    app = Mock()
    app.results = []
    app.repo.xpath.side_effect = lambda key: key
    app.ui.text.return_value = 'VIEW ALL COHORTS(0)'
    option = app.ui.visible.return_value
    option.is_visible.return_value = True
    monkeypatch.setattr(cohort, '_selected_option_is_enabled', lambda _: enabled)
    monkeypatch.setattr(cohort, 'expect', lambda _: Mock())
    cohort.verify_selected_participants_option(app, state)
    app.ui.click.assert_called_once_with('Cohort/CreateNew', repo_key='Cohort/CreateNew')
    assert app.page.locator.call_args.args == ('Statbar/Participants-Count',)
    app.page.locator.return_value.click.assert_called_once()
    assert option.click.call_count == (0 if enabled else 1)
    assert app.results[0]['status'] == 'PASSED'


def test_selected_excel_case_uses_only_study_and_first_two_pages():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC02_C3DC_Verify_Create_NewCohort_SelectedParticipants.xlsx'))
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter',
        'verify_selected_participants_option', 'select_participant_page', 'select_participant_page',
        'verify_selected_participants_option', 'create_cohort_from_selected_participants',
        'verify_cohort_created', 'assert_no_failures',
    ]
    app.select_filter.assert_called_once_with('Study/dbGaP_Accession', 'phs002790')
    assert [call.args for call in app.select_participant_page.call_args_list] == [(1,), (2,)]
    assert [call.args for call in app.verify_selected_participants_option.call_args_list] == [('disabled',), ('enabled',)]
    app.load_query_file.assert_not_called()


def limit_app(monkeypatch, before=1):
    from Commons.apps.c3dc import cohort
    app = cohort_app()
    app.repo = Mock()
    app.repo.xpath.side_effect = lambda key: key
    dialog = Mock()
    dialog.locator.return_value.count.return_value = before
    monkeypatch.setattr(cohort, 'cohort_dialog', lambda _: dialog)
    source = CohortDetails('New Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")))
    read = Mock(return_value=source)
    monkeypatch.setattr(cohort, 'read_selected_cohort', read)
    duplicate = Mock()
    monkeypatch.setattr(cohort, 'duplicate_selected_cohort', duplicate)
    return app, source, duplicate, read


def test_limit_workflow_performs_and_verifies_exactly_19_duplicates(monkeypatch):
    from Commons.apps.c3dc.cohort import duplicate_cohort_repeatedly
    app, source, duplicate, read = limit_app(monkeypatch)
    duplicate_cohort_repeatedly(app, 19)
    assert duplicate.call_count == 19
    assert read.call_count == 20  # Original snapshot plus every new copy.
    assert len([r for r in app.results if r['check'].startswith('Duplicate ')]) == 19
    assert app._cohort_limit_source == source


@pytest.mark.parametrize('count', [0, -1])
def test_repeat_duplicate_rejects_invalid_count(monkeypatch, count):
    from Commons.apps.c3dc.cohort import duplicate_cohort_repeatedly
    app, _, duplicate, _ = limit_app(monkeypatch)
    with pytest.raises(ValueError, match='at least 1'):
        duplicate_cohort_repeatedly(app, count)
    duplicate.assert_not_called()


def test_repeat_duplicate_rejects_request_that_exceeds_limit(monkeypatch):
    from Commons.apps.c3dc.cohort import duplicate_cohort_repeatedly
    app, _, duplicate, _ = limit_app(monkeypatch, before=2)
    with pytest.raises(AssertionError, match='maximum is 20'):
        duplicate_cohort_repeatedly(app, 19)
    duplicate.assert_not_called()


def test_repeat_duplicate_stops_if_copy_verification_fails(monkeypatch):
    from Commons.apps.c3dc.cohort import duplicate_cohort_repeatedly
    app, source, duplicate, read = limit_app(monkeypatch)
    read.side_effect = [source, CohortDetails('New Cohort (Copy)', 2, (("P1", "phs002790"), ("WRONG", "phs002790")))]
    with pytest.raises(AssertionError, match='Duplicate 1 of 19 failed'):
        duplicate_cohort_repeatedly(app, 19)
    assert duplicate.call_count == 1
    assert read.call_count == 2


def test_limit_excel_case_runs_19_duplicates_then_checks_ui_limit():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC04_C3DC_Verify_Duplicate_Cohort_CreationLimit.xlsx'))
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter', 'select_filter',
        'create_cohort_from_all_participants', 'verify_cohort_created',
        'close_cohorts', 'open_cohorts', 'duplicate_cohort_repeatedly',
        'verify_duplicate_cohort_limit', 'assert_no_failures',
    ]
    app.duplicate_cohort_repeatedly.assert_called_once_with(19)
    app.load_query_file.assert_not_called()


def cohort_edit_baseline():
    original = CohortDetails('New Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")))
    edit = CohortEdit(original, 'Updated AIAN Cohort', 'Saved cohort description.', 1)
    actual = CohortDetails(edit.name, 2, tuple(reversed(original.participants)), edit.description)
    return edit, actual


def test_saved_metadata_preserves_membership_regardless_of_sort_order():
    from Commons.apps.c3dc.cohort import _cohort_edit_checks
    edit, actual = cohort_edit_baseline()
    assert all(_cohort_edit_checks(edit, actual, 1).values())


@pytest.mark.parametrize('actual,count,failed_check', [
    (CohortDetails('New Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")), 'Saved cohort description.'), 1, 'saved name'),
    (CohortDetails('Updated AIAN Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")), ''), 1, 'saved description'),
    (CohortDetails('Updated AIAN Cohort', 2, (("P1", "phs002790"), ("P2", "phs002790")), 'Saved cohort description.'), 2, 'cohort count unchanged'),
    (CohortDetails('Updated AIAN Cohort', 1, (("P1", "phs002790"),), 'Saved cohort description.'), 1, 'participant count unchanged'),
    (CohortDetails('Updated AIAN Cohort', 2, (("P1", "phs002790"), ("P1", "phs002790")), 'Saved cohort description.'), 1, 'unique participant rows'),
    (CohortDetails('Updated AIAN Cohort', 2, (("P1", "phs000463"), ("P2", "phs002790")), 'Saved cohort description.'), 1, 'participant and study IDs unchanged'),
])
def test_saved_metadata_rejects_lost_changes_or_membership_edits(actual, count, failed_check):
    from Commons.apps.c3dc.cohort import _cohort_edit_checks
    edit, _ = cohort_edit_baseline()
    assert not _cohort_edit_checks(edit, actual, count)[failed_check]


def test_metadata_verification_requires_save_not_just_entered_drafts():
    from Commons.apps.c3dc.cohort import verify_cohort_details_saved
    app = cohort_app()
    app._cohort_edit, _ = cohort_edit_baseline()
    app._cohort_edit_saved = False
    with pytest.raises(AssertionError, match='Save cohort changes before'):
        verify_cohort_details_saved(app)


def test_save_requires_an_edit_baseline():
    from Commons.apps.c3dc.cohort import save_cohort_changes
    with pytest.raises(AssertionError, match='Update cohort details before'):
        save_cohort_changes(C3DC.__new__(C3DC))


def test_update_rejects_blank_name_before_editing_ui():
    from Commons.apps.c3dc.cohort import update_cohort_details
    app = Mock()
    with pytest.raises(ValueError, match='nonempty cohort name'):
        update_cohort_details(app, '  ', 'Description')
    app.ui.click.assert_not_called()
    assert app._cohort_edit is None and app._cohort_edit_saved is False


def test_metadata_excel_case_edits_saves_then_verifies_persistence():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC05_C3DC_Verify_Update_Cohort_Name_Description.xlsx'))
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_filter', 'select_filter',
        'create_cohort_from_all_participants', 'verify_cohort_created',
        'update_cohort_details', 'save_cohort_changes', 'verify_cohort_details_saved',
        'assert_no_failures',
    ]
    app.update_cohort_details.assert_called_once_with(
        'Updated AIAN Cohort',
        'Participants from study phs002790 with race American Indian or Alaska Native. Updated cohort description.',
    )
    app.load_query_file.assert_not_called()


def test_duplicate_name_case_creates_once_then_duplicates_and_checks_rejection():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC12_C3DC_Verify_Duplicate_Cohort_Name.xlsx'))
    assert [step[0] for step in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_participant_page',
        'create_cohort_from_selected_participants', 'verify_cohort_created',
        'update_cohort_details', 'save_cohort_changes', 'verify_cohort_details_saved',
        'duplicate_selected_cohort', 'update_cohort_details',
        'verify_duplicate_cohort_name_rejected', 'assert_no_failures',
    ]
    app.select_participant_page.assert_called_once_with(1)
    assert [step.args for step in app.update_cohort_details.call_args_list] == [('AutoTest', ''), ('AutoTest', '')]
    app.verify_duplicate_cohort_name_rejected.assert_called_once_with(
        'Failed to update cohort: Cohort with Name AutoTest already exists, please choose a different name'
    )
    app.load_query_file.assert_not_called()


def test_duplicate_name_rejection_requires_a_different_cohort_edit():
    from Commons.apps.c3dc.cohort import verify_duplicate_cohort_name_rejected
    app = C3DC.__new__(C3DC)
    with pytest.raises(AssertionError, match='Edit a different cohort'):
        verify_duplicate_cohort_name_rejected(app, 'error')
    original = CohortDetails('AutoTest', 2, PARTICIPANTS)
    app._cohort_edit = CohortEdit(original, 'AutoTest', '', 2)
    with pytest.raises(AssertionError, match='Edit a different cohort'):
        verify_duplicate_cohort_name_rejected(app, 'error')


def test_participant_search_removal_case_saves_then_verifies_persistence():
    app = Mock(NAME='C3DC', spec=C3DC)
    run_testcase_excel(app, CASE.with_name('TC13_C3DC_Verify_Cohort_Participant_Search_Removal.xlsx'))
    assert [step[0] for step in app.method_calls] == [
        'accept_banner', 'open_explore', 'select_participant_page',
        'create_cohort_from_selected_participants', 'verify_cohort_created',
        'verify_cohort_participant_search', 'remove_cohort_participant',
        'verify_cohort_participant_removed', 'assert_no_failures',
    ]
    app.select_participant_page.assert_called_once_with(1)
    app.load_query_file.assert_not_called()


@pytest.mark.parametrize('action,message', [
    ('remove_cohort_participant', 'Verify participant search before'),
    ('verify_cohort_participant_removed', 'Remove and save a participant before'),
])
def test_participant_removal_requires_its_ui_baseline(action, message):
    from Commons.apps.c3dc import cohort
    with pytest.raises(AssertionError, match=message):
        getattr(cohort, action)(C3DC.__new__(C3DC))
