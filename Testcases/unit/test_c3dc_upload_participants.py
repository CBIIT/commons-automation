"""Upload input contracts and executable Excel action wiring."""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from Commons.apps.c3dc.app import C3DC
from Commons.apps.c3dc import upload_participants as upload
from Testcases.unit.python_cases import run_python_case, case_report_name

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_typed_ids_preserve_leading_zeros_and_separator():
    app = Mock()
    with patch.object(upload, '_dialog'), patch.object(upload, '_control') as control:
        upload.type_participant_ids(app, ['001A', '002B'], separator=', ')
    control.return_value.fill.assert_called_once_with('001A, 002B')


def test_literal_input_preserves_whitespace_for_validation():
    app = Mock()
    with patch.object(upload, '_dialog'), patch.object(upload, '_control') as control:
        upload.type_participant_ids(app, ' 001A,\n002B,')
    control.return_value.fill.assert_called_once_with(' 001A,\n002B,')


def test_missing_file_fails_before_browser_action(tmp_path):
    with pytest.raises(FileNotFoundError):
        upload.attach_participant_file(Mock(), tmp_path / 'missing.tsv')


def test_preview_rejects_wrong_membership_even_with_equal_counts():
    app = Mock()
    app.ui.timeout_ms = 0
    expected = upload.ParticipantUpload(('001A',), ('UNKNOWN',))
    with patch.object(upload, '_dialog'), patch.object(upload, 'expect'), patch.object(upload, 'read_upload_summary', side_effect=[('WRONG',), ('UNKNOWN',)]):
        with pytest.raises(AssertionError, match='matched preview:'):
            upload.verify_upload_preview(app, expected)


def test_preview_waits_for_replacement_ids_when_counts_do_not_change():
    app = Mock()
    app.ui.timeout_ms = 1000
    expected = upload.ParticipantUpload(('NEW',), ('NEW-UNKNOWN',))
    with patch.object(upload, '_dialog'), patch.object(upload, 'expect'), patch.object(
        upload, 'read_upload_summary', side_effect=[
            ('OLD',), ('OLD-UNKNOWN',), ('NEW',), ('NEW-UNKNOWN',)]
    ):
        assert upload.verify_upload_preview(app, expected) == {
            'matched': ('NEW',), 'unmatched': ('NEW-UNKNOWN',)}
    app.page.wait_for_timeout.assert_called_once_with(100)


def test_tc01_dispatches_dynamic_baseline_and_exact_result_checks():
    app = Mock(spec=C3DC)
    path = ROOT / 'Testcases/C3DC/upload_participants/test_TC01_C3DC_Verify_Upload_Participants_TypedIDs.py'
    run_python_case(app, path)
    app.prepare_participant_upload.assert_called_once_with(2, 1)
    app.type_participant_ids.assert_called_once_with(None)
    app.verify_upload_preview.assert_called_once_with()
    app.submit_participant_upload.assert_called_once_with()
    app.verify_uploaded_participants.assert_called_once_with(case_report_name(path))
    app.assert_no_failures.assert_called_once_with()


def test_reading_open_summary_does_not_toggle_it_closed():
    details = Mock()
    details.is_visible.return_value = True
    details.inner_text.return_value = 'Submitted Participant ID\n001A\n002B'
    count = Mock()
    count.inner_text.return_value = '2'
    heading = Mock()
    controls = {'MatchedCount': count, 'MatchedTable': details, 'Matched': heading}
    with patch.object(upload, '_dialog'), patch.object(upload, 'expect'), patch.object(upload, '_control', side_effect=lambda app, key, scope: controls[key]):
        assert upload.read_upload_summary(Mock(), 'matched') == ('001A', '002B')
    heading.click.assert_not_called()


def test_text_file_preserves_ids_and_newlines(tmp_path):
    path = upload.write_participant_file(tmp_path / 'nested' / 'participants.txt', ('001A', '002B', 'UNMATCHED'))
    assert path.read_text(encoding='utf-8') == '001A\n002B\nUNMATCHED\n'


def test_file_writer_rejects_single_string_instead_of_writing_characters(tmp_path):
    with pytest.raises(TypeError, match='sequence of IDs'):
        upload.write_participant_file(tmp_path / 'participants.txt', '001A')


@pytest.mark.parametrize('case_name,filename', [
    ('test_TC02_C3DC_Verify_Upload_Participants_TextFile.py', 'participants.txt'),
    ('test_TC03_C3DC_Verify_Upload_Participants_CsvFile.py', 'participants.csv'),
])
def test_file_case_creates_and_attaches_generated_file(case_name, filename):
    app = Mock(spec=C3DC)
    path = ROOT / 'Testcases/C3DC/upload_participants' / case_name
    run_python_case(app, path)
    app.create_participant_upload_file.assert_called_once_with(case_report_name(path), filename)
    app.attach_participant_file.assert_called_once_with(None)
    app.type_participant_ids.assert_not_called()
    app.verify_upload_preview.assert_called_once_with()
    app.verify_uploaded_participants.assert_called_once_with(case_report_name(path))


def test_csv_file_has_comma_delimited_ids_and_preserves_leading_zeros(tmp_path):
    import csv
    ids = ('001A', '002B', 'UNMATCHED')
    path = upload.write_participant_file(tmp_path / 'participants.csv', ids)
    assert path.read_text(encoding='utf-8').strip() == '001A,002B,UNMATCHED'
    with path.open(encoding='utf-8', newline='') as stream:
        assert list(csv.reader(stream)) == [list(ids)]


def test_update_fixture_captures_disjoint_sets_before_filtering():
    pool = upload.ParticipantUpload(('001A', '002B', '003C', '004D'), ('UNKNOWN1', 'UNKNOWN2'))
    with patch.object(upload, 'prepare_participant_upload', return_value=pool) as prepare:
        original, replacement = upload.prepare_participant_upload_update(Mock(), 2, 1)
    assert original == upload.ParticipantUpload(('001A', '002B'), ('UNKNOWN1',))
    assert replacement == upload.ParticipantUpload(('003C', '004D'), ('UNKNOWN2',))
    assert set(original.submitted).isdisjoint(replacement.submitted)
    assert prepare.call_args.args[1:] == (4, 2)


def test_tc05_verifies_retained_input_and_both_result_sets():
    app = Mock(spec=C3DC)
    path = ROOT / 'Testcases/C3DC/upload_participants/test_TC05_C3DC_Verify_View_Update_Participants_Set.py'
    run_python_case(app, path)
    app.prepare_participant_upload_update.assert_called_once_with(2, 1)
    app.use_replacement_participant_upload.assert_called_once_with()
    assert app.verify_participant_upload_draft.call_count == 2
    assert app.verify_uploaded_participants.call_count == 2
    assert app.submit_participant_upload.call_count == 2
    app.cancel_participant_upload.assert_called_once_with()


def test_limit_case_dispatches_text_file_check_only():
    app = Mock(spec=C3DC)
    path = ROOT / 'Testcases/C3DC/upload_participants/test_TC04_C3DC_Verify_Upload_Participants_Limit.py'
    run_python_case(app, path)
    app.verify_participant_upload_limit.assert_called_once_with(1500, case_report_name(path))
    app.assert_no_failures.assert_called_once_with()


def test_limit_check_rejects_invalid_configuration():
    with pytest.raises(ValueError, match='positive limit'):
        upload.verify_participant_upload_limit(Mock(), 0, 'boundary')


def test_limit_check_uses_files_and_counts_without_reading_results_table(tmp_path):
    from contextlib import ExitStack
    app = Mock()
    app.output_dir = tmp_path
    app.failures = []
    with ExitStack() as stack:
        enter = stack.enter_context(patch.object(upload, '_upload_boundary_file'))
        source = stack.enter_context(patch.object(upload, 'fetch_upload_source_ids', return_value=('001A', '002B', '003C', '004D')))
        table = stack.enter_context(patch.object(upload, 'read_uploaded_participant_ids'))
        for name in ('verify_upload_preview', 'submit_participant_upload', 'verify_uploaded_participant_count', 'verify_upload_limit_rejected'):
            stack.enter_context(patch.object(upload, name))
        upload.verify_participant_upload_limit(app, 3, 'boundary.xlsx')
    source.assert_called_once_with(app, 4)
    table.assert_not_called()
    assert enter.call_args_list[0].args[1].matched == ('001A', '002B', '003C')
    assert enter.call_args_list[1].args[1].matched == ('001A', '002B', '003C', '004D')


def test_boundary_source_reuses_request_with_one_api_call():
    import json
    app = Mock()
    request = Mock()
    request.url = 'https://example.test/graphql'
    request.post_data = json.dumps({'variables': {'first': 50, 'offset': 100, 'sort_direction': 'asc'}})
    app._cohort_participant_response = (Mock(request=request), {})
    response = app.page.request.post.return_value
    response.ok = True
    response.json.return_value = {'data': {'participantOverview': [{'participant_id': '001A'}, {'participant_id': '002B'}, {'participant_id': 'hashlower'}]}}
    with patch.object(upload, 'expect'), patch.object(upload, '_control'):
        assert upload.fetch_upload_source_ids(app, 2) == ('001A', '002B')
    app.page.request.post.assert_called_once()
    assert app.page.request.post.call_args.kwargs['data']['variables'] == {'first': 4, 'offset': 0, 'sort_direction': 'desc'}


def test_tc06_checks_cancel_close_clear_and_chip_removal():
    app = Mock(spec=C3DC)
    path = ROOT / 'Testcases/C3DC/upload_participants/test_TC06_C3DC_Verify_Participants_Set_Clear_Cancel_Remove.py'
    run_python_case(app, path)
    app.remember_participant_upload_baseline.assert_called_once_with()
    app.cancel_participant_upload.assert_called_once_with()
    app.close_participant_upload.assert_called_once_with()
    app.clear_participant_upload.assert_called_once_with()
    app.remove_participant_upload.assert_called_once_with()
    app.verify_participant_upload_empty.assert_called_once_with()
    assert app.verify_participant_upload_cleared.call_count == 2
    assert app.verify_uploaded_participants.call_count == 3


def test_cancel_draft_does_not_replace_the_original_expected_set():
    app = C3DC.__new__(C3DC)
    app._participant_upload = upload.ParticipantUpload(('001A',))
    app._participant_upload_replacement = upload.ParticipantUpload(('002B',))
    with patch.object(upload, 'type_participant_ids') as type_ids:
        app.type_replacement_participant_ids()
    assert app._participant_upload.matched == ('001A',)
    type_ids.assert_called_once_with(app, ('002B',))


def test_remove_upload_refuses_to_clear_other_active_filters():
    app = Mock()
    app.page.url = 'https://example.test/exploreParticipants?u=001A&race=Asian'
    with patch.object(upload, '_control') as control:
        with pytest.raises(AssertionError, match='other active filters'):
            upload.remove_participant_upload(app)
    control.assert_not_called()


def test_tc07_dispatches_documented_unmatched_scenario():
    app = Mock(spec=C3DC)
    name = 'test_TC07_C3DC_Verify_Unmatched_Participants.py'
    run_python_case(app, ROOT / 'Testcases/C3DC/upload_participants' / name)
    app.verify_unmatched_participants.assert_called_once_with(3, case_report_name(name))
    app.assert_no_failures.assert_called_once_with()


@pytest.mark.parametrize('query,view_visible,total,marker,errors', [
    ('', True, '66,756', False, 0),
    ('?u=INVALID', True, '66,756', False, 1),
    ('', True, '66,756', True, 1),
    ('', True, '1', False, 1),
    ('', False, '66,756', False, 1),
])
def test_unmatched_submission_requires_no_filter_unchanged_total_and_view(query, view_visible, total, marker, errors):
    app = Mock()
    app.page.url = 'https://example.test/exploreParticipants' + query
    app.page.locator.return_value.inner_text.return_value = total
    controls = {'View': Mock(), 'InputSet': Mock()}
    controls['View'].is_visible.return_value = view_visible
    controls['InputSet'].is_visible.return_value = marker
    with patch.object(upload, '_control', side_effect=lambda app, name: controls[name]):
        upload._check_unmatched_submission(app, 66756)
    assert app._fail.call_count == errors


def test_unmatched_count_must_be_positive():
    with pytest.raises(ValueError, match='at least one'):
        upload.verify_unmatched_participants(Mock(), 0, 'case.xlsx')


def test_formatted_ids_preserve_case_zeros_and_deliberate_duplicates():
    assert upload.format_participant_ids(('001Ab', '002CD')) == ' 001Ab ,\n 002CD ,\n 001Ab ,\n 002CD ,\n'
    assert upload.format_participant_ids(('001A',), separator=';', repetitions=1, padding='', trailing_separator=False) == '001A'


def test_tc08_submits_formatted_ids_against_unique_baseline():
    app = Mock(spec=C3DC)
    name = 'test_TC08_C3DC_Verify_Participants_Set_Duplicates_Formatting.py'
    run_python_case(app, ROOT / 'Testcases/C3DC/upload_participants' / name)
    app.prepare_participant_upload.assert_called_once_with(2, 0)
    app.type_formatted_participant_ids.assert_called_once_with(2)
    app.verify_upload_preview.assert_called_once_with()
    app.submit_participant_upload.assert_called_once_with()
    app.verify_uploaded_participants.assert_called_once_with(case_report_name(name))
    app.assert_no_failures.assert_called_once_with()


def test_formatted_typing_does_not_mutate_expected_upload():
    app = C3DC.__new__(C3DC)
    expected = app._participant_upload = upload.ParticipantUpload(('001A', '002B'))
    with patch.object(upload, 'type_participant_ids') as type_ids:
        app.type_formatted_participant_ids(2)
    type_ids.assert_called_once_with(app, ' 001A ,\n 002B ,\n 001A ,\n 002B ,\n')
    assert app._participant_upload == expected
