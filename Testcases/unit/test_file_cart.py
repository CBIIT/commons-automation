"""Shared cart contracts: independent membership, metadata and artifact validation."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.file_cart import (FileRecord, compare_records, file_size_bytes, normalize_value,
                               records_from_cells, verify_csv_manifest)
from Commons.apps.c3dc.app import C3DC
from Commons.apps.gc.app import GC
from Commons.apps.icdc.app import ICDC
from Commons.apps.ctdc.app import CTDC
from Commons.excel_testcase.registry import get_profile
from Commons.excel_testcase.runner import run_testcase_excel
from Commons.excel_testcase.file_cart_steps import c3dc_cart_handlers

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def record(name='example.txt', **values):
    return FileRecord(tuple({'name': name, **values}.items()))


def test_rows_are_resolved_by_header_not_position():
    assert records_from_cells(['Sample ID', '', 'File Name'], [['S2\nS1', '', 'a.txt']],
                              {'name': 'File Name', 'samples': 'Sample ID'}) == (record('a.txt', samples='S1;S2'),)


@pytest.mark.parametrize('headers,rows,match', [
    (['Wrong Name'], [['a']], 'column'),
    (['File Name', 'File Name'], [['a', 'a']], 'column'),
    (['File Name'], [['a'], ['a']], 'ambiguous'),
    (['File Name'], [['']], 'empty name'),
])
def test_schema_or_identity_ambiguity_fails(headers, rows, match):
    with pytest.raises(AssertionError, match=match):
        records_from_cells(headers, rows, {'name': 'File Name'})


def test_empty_cart_colspan_is_not_a_file():
    assert records_from_cells(['File Name', 'Study'], [['No Matching Records Found']], {'name': 'File Name'}) == ()


def test_same_count_different_files_is_a_mismatch():
    diff = compare_records((record('a'),), (record('b'),))
    assert diff['missing'] == ['a'] and diff['unexpected'] == ['b']


def test_metadata_changes_cannot_pass_with_matching_names():
    diff = compare_records((record(study='one'),), (record(study='two'),))
    assert diff['changed']['example.txt']['expected']['study'] == 'one'


def test_additional_display_columns_do_not_erase_source_baseline():
    assert not any(compare_records((record(study='one'),), (record(study='one', size='2 MB'),)).values())


def test_duplicate_cart_rows_cannot_be_hidden_by_dictionary_conversion():
    with pytest.raises(AssertionError, match='duplicate'):
        compare_records((record(),), (record(), record()))


def test_participant_lists_normalize_separators_without_changing_ids():
    assert normalize_value('participants', '002B,001a\n002B;003C') == '001a;002B;003C'
    assert normalize_value('name', 'a,b.txt') == 'a,b.txt'


@pytest.mark.parametrize('value,expected', [('2 GB', 2*1024**3), ('25.65 MB', 25.65*1024**2), ('1,024 B', 1024)])
def test_size_sort_keys_are_numeric(value, expected):
    assert file_size_bytes(value) == expected


@pytest.mark.parametrize('body,passes', [
    ('name,Participant ID\na.txt,P2;P1\n', True),
    ('name,Participant ID\nb.txt,P2;P1\n', False),
    ('name,Participant ID\na.txt,P3;P1\n', False),
    ('name,Participant ID\na.txt,P2;P1\na.txt,P2;P1\n', False),
    ('wrong,Participant ID\na.txt,P2;P1\n', False),
])
def test_csv_manifest_checks_membership_schema_and_participants(tmp_path, body, passes):
    path = tmp_path / 'manifest.csv'
    path.write_text(body, encoding='utf-8-sig')
    expected = (record('a.txt', participants='P1;P2'),)
    if passes:
        assert len(verify_csv_manifest(path, expected, name_column='name', participant_column='Participant ID')) == 1
    else:
        with pytest.raises(AssertionError):
            verify_csv_manifest(path, expected, name_column='name', participant_column='Participant ID')


@pytest.mark.parametrize('app_type', [C3DC, GC, ICDC, CTDC])
def test_each_app_owns_its_adapter_and_expected_state(app_type):
    first, second = app_type.__new__(app_type), app_type.__new__(app_type)
    assert first.file_cart is first.file_cart
    assert first.file_cart is not second.file_cart
    assert first.file_cart.app is first
    first.file_cart.expected['a'] = record('a')
    assert not second.file_cart.expected
    assert get_profile(app_type.NAME).case_subdirs[0] == 'studies'


@pytest.mark.parametrize('case', sorted((ROOT / 'Testcases/C3DC/file_cart').glob('TC*.xlsx')), ids=lambda p:p.stem)
def test_c3dc_cart_workbooks_dispatch(case):
    app = Mock(spec=C3DC)
    run_testcase_excel(app, case)
    app.accept_banner.assert_called_once_with()
    app.assert_no_failures.assert_called_once_with()
    assert any(call[0].startswith('file_cart.') for call in app.method_calls)


def test_remove_all_requires_explicit_decision():
    app = Mock()
    with pytest.raises(ValueError, match='confirm or cancel'):
        c3dc_cart_handlers()['remove_all_cart_files'](app, '', 'typo', '', '')
    app.file_cart.remove_all.assert_not_called()


def test_same_name_files_from_different_studies_remain_distinct():
    headers = ['File Name', 'Study ID']
    rows = [['same.bam', 'study-one'], ['same.bam', 'study-two']]
    records = records_from_cells(headers, rows, {'name': 'File Name', 'study': 'Study ID'}, ('name', 'study'))
    assert len({r.identity for r in records}) == 2
    assert not any(compare_records(records, records[::-1]).values())


def test_source_parsing_does_not_drop_duplicate_representations():
    records = records_from_cells(['File Name'], [['a'], ['a']], {'name': 'File Name'}, require_unique=False)
    assert len(records) == 2
    with pytest.raises(AssertionError, match='ambiguous'):
        records_from_cells(['File Name'], [['a'], ['a']], {'name': 'File Name'})


def test_file_name_identity_preserves_internal_whitespace():
    assert record('a  b.txt').identity != record('a b.txt').identity


def test_manifest_allows_distinct_files_with_the_same_name(tmp_path):
    path = tmp_path / 'manifest.csv'
    path.write_text('name,Participant ID,drs_uri\nsame.bam,P1,drs://one\nsame.bam,P2,drs://two\n')
    expected = (record('same.bam', participants='P1'), record('same.bam', participants='P2'))
    assert len(verify_csv_manifest(path, expected, name_column='name', participant_column='Participant ID', required_columns=('drs_uri',))) == 2


def test_manifest_rejects_repeated_drs_identity_even_with_correct_names(tmp_path):
    path = tmp_path / 'manifest.csv'
    path.write_text('name,drs_uri\na.bam,drs://one\nb.bam,drs://one\n')
    with pytest.raises(AssertionError, match='DRS file identity'):
        verify_csv_manifest(path, (record('a.bam'), record('b.bam')), name_column='name', required_columns=('drs_uri',))


def test_full_page_selection_uses_one_header_click_without_row_clicks():
    from unittest.mock import patch
    from Commons.file_cart import FileCart
    cart = FileCart(Mock())
    table = Mock()
    rows = tuple(record(f'file-{index}.txt') for index in range(50))
    with patch.object(cart, 'visible', return_value=table), patch.object(cart, 'read_page', return_value=rows), patch('Commons.file_cart.expect') as expect:
        cart.select_files(0)
    table.locator.return_value.check.assert_called_once_with()
    assert any(call.args == ('thead input[type=checkbox]',) for call in table.locator.call_args_list)
    assert not any(call.args == ('tbody tr',) for call in table.locator.call_args_list)
    expect.return_value.to_have_count.assert_called_once_with(50)
    assert tuple(cart.selected.values()) == rows


@pytest.mark.parametrize('app_name,app_type', [('GC', GC), ('CTDC', CTDC), ('ICDC', ICDC)])
def test_bento_cart_suites_dispatch_and_are_in_regression(app_name, app_type):
    """Workbook actions must reach the app adapter and remain discoverable in CI."""
    import yaml
    suite = yaml.safe_load((ROOT / 'Config/suites.yaml').read_text())[app_name]['regression']
    assert 'file_cart/TC*.xlsx' in suite
    cases = sorted((ROOT / 'Testcases' / app_name / 'file_cart').glob('TC*.xlsx'))
    assert cases
    for case in cases:
        app = Mock(spec=app_type)
        run_testcase_excel(app, case)
        app.accept_banner.assert_called_once_with()
        app.assert_no_failures.assert_called_once_with()
        assert any(call[0].startswith('file_cart.') for call in app.method_calls)


def test_gc_selection_keeps_distinguishable_files_without_merging_source_rows():
    """GC's cart lacks File ID, so ambiguous fixture rows must remain unselected."""
    from unittest.mock import patch
    from Commons.apps.gc.file_cart import GCFileCart
    cart = GCFileCart(Mock())
    rows = (record('a.bam'), record('a.bam'), record('b.bam'), record('c.bam'))
    table = Mock()
    with patch.object(cart, 'read_page', return_value=rows), patch.object(cart, 'visible', return_value=table):
        cart.select_files(3)
    assert tuple(cart.selected) == ('a.bam', 'b.bam', 'c.bam')
    assert [call.args[0] for call in table.locator.return_value.nth.call_args_list] == [0, 2, 3]


def test_gc_refuses_insufficient_distinguishable_rows():
    from unittest.mock import patch
    from Commons.apps.gc.file_cart import GCFileCart
    cart = GCFileCart(Mock())
    with patch.object(cart, 'read_page', return_value=(record(), record())), pytest.raises(AssertionError, match='distinguishable'):
        cart.select_files(2)
    assert not cart.selected


def test_selected_manifest_rejects_unselected_file(tmp_path):
    path = tmp_path / 'selected.csv'
    path.write_text('name,Case ID,drs_uri\na.txt,C1,drs://one\nb.txt,C2,drs://two\n')
    with pytest.raises(AssertionError, match='membership differs'):
        verify_csv_manifest(path, (record('a.txt', participants='C1'),), name_column='name',
                            participant_column='Case ID', required_columns=('drs_uri',))


@pytest.mark.parametrize('app_type,participant_column,checksum_column', [
    (GC, None, 'Md5sum'), (CTDC, 'participant_id', 'Md5sum'), (ICDC, 'Case ID', 'md5sum'),
])
def test_app_manifest_verification_uses_selected_subset_and_portal_schema(
        tmp_path, app_type, participant_column, checksum_column):
    import csv
    app = Mock(results=[])
    cart = app_type.FILE_CART_CLASS(app)
    selected = record('selected.txt', participants='P1;P2')
    cart.expected = {'selected.txt': selected, 'other.txt': record('other.txt', participants='P3')}
    cart.export_records = (selected,)
    cart.manifest_path = tmp_path / 'manifest.csv'
    row = {'name': 'selected.txt', 'drs_uri': 'drs://selected', checksum_column: 'a' * 32,
           'Accession': 'study', 'Sample Id': 'S1'}
    if participant_column:
        row[participant_column] = 'P2;P1'
    with cart.manifest_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    cart.verify_manifest()
    assert len(cart.expected) == 2
    assert app.results[-1]['status'] == 'PASSED'
    # A file with the right name must still fail if the portal schema is missing.
    cart.manifest_path.write_text('name,drs_uri\nselected.txt,drs://selected\n')
    with pytest.raises(AssertionError, match='manifest headers'):
        cart.verify_manifest()


@pytest.mark.parametrize('app_type,confirm_label,cancel_label', [
    (GC, 'OK', 'Cancel'), (CTDC, 'Yes', 'No'), (ICDC, 'OK', 'Cancel'),
])
@pytest.mark.parametrize('confirm', [False, True])
def test_app_removal_preserves_cancel_and_confirm_behavior(app_type, confirm_label, cancel_label, confirm):
    from unittest.mock import patch
    cart = app_type.FILE_CART_CLASS(Mock())
    original = {'a.txt': record('a.txt')}
    cart.expected = dict(original)
    dialog = Mock()
    with patch.object(cart, 'visible', return_value=dialog), patch.object(cart, 'control'), \
            patch.object(cart, 'wait_for_total') as wait, patch('Commons.file_cart.expect'):
        cart.remove_all(confirm)
    label = dialog.get_by_role.call_args.kwargs['name']
    assert label.fullmatch(confirm_label if confirm else cancel_label)
    assert cart.expected == ({} if confirm else original)
    wait.assert_called_once_with(0 if confirm else 1)
