"""Cross-portal exports must retain strict independent-data verification."""
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps import APPS
from Commons.db_source import Table
from Commons.excel_testcase.registry import get_profile
from Commons.excel_testcase.runner import run_testcase_excel
from Commons.result_tabs import compare_export
from Commons.table_sorting import SortRule, assert_sorted

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_null_order_is_explicit_and_does_not_weaken_the_default():
    assert_sorted([None, 0, 2], 'asc', nulls_smallest=True)
    assert_sorted([2, 0, None], 'desc', nulls_smallest=True)
    with pytest.raises(AssertionError):
        assert_sorted([None, 0, 2], 'asc')
    with pytest.raises(AssertionError):
        assert_sorted([None, 2, 0], 'asc', nulls_smallest=True)


@pytest.mark.parametrize('value,number', [('1.5 KB', 1536), ('2 MB', 2097152), ('999 B', 999), ('10 Bytes', 10)])
def test_file_sizes_are_compared_in_bytes(value, number):
    assert SortRule(kind='size').key(value, 'asc') == Decimal(number)


@pytest.mark.parametrize('value', ['Unknown', '1 PB', '1.2'])
def test_unrecognized_sizes_cannot_silently_sort_as_text(value):
    with pytest.raises(AssertionError, match='Invalid file size'):
        SortRule(kind='size').key(value, 'asc')


@pytest.mark.parametrize('app', ['GC', 'CTDC', 'ICDC', 'INS', 'PSDC'])
def test_csv_only_adapters_reject_unavailable_json_before_download(app):
    helper = APPS[app].RESULT_TABS_CLASS(Mock())
    with pytest.raises(ValueError, match='CSV only'):
        helper.export_spec(next(iter(helper.EXPORTS)), 'JSON')


def test_icdc_numeric_and_size_formatting_does_not_hide_changed_metadata():
    helper = APPS['ICDC'].RESULT_TABS_CLASS(Mock())
    headers = ['File UUID', 'Weight (kg)', 'Size', 'Description']
    expected = Table(headers, [['file-1', '47.0', '1024', 'Original']])
    actual = Table(headers, [['file-1', '47', '1 KB', 'Changed']])
    expected, actual = helper.prepare_comparison('Case Files', expected, actual)
    assert expected.rows[0][1:3] == actual.rows[0][1:3]
    assert all(compare_export(expected, actual, ('File UUID',)).values())


@pytest.mark.parametrize('app', ['GC', 'CTDC', 'ICDC', 'INS', 'PSDC', 'Bento'])
def test_excel_sorting_cases_dispatch_through_shared_action(app):
    import openpyxl
    profile = get_profile(app)
    cases = sorted((ROOT/'Testcases'/profile.testcases_dir/'result_tabs').rglob('*Sorting.xlsx'))
    assert len(cases) == len(APPS[app].TABS)
    for case in cases:
        mock = Mock(spec=APPS[app])
        run_testcase_excel(mock, case)
        mock.verify_result_tab_sorting.assert_called_once()
        mock.load_query_file.assert_not_called()
        workbook = openpyxl.load_workbook(case)
        assert workbook['_Lists'].sheet_state == 'hidden'
        assert 'ResultTabActions' in workbook.defined_names
        workbook.close()


def test_ctdc_sorting_preserves_complete_regimen_labels():
    from Commons.apps.ctdc.table_sorting import sorting_options
    app = Mock()
    options = sorting_options(app, 'Participants')
    response = Mock(url='https://clinical.test/graphql')
    response.request.method = 'POST'
    response.request.post_data_json = {'operationName': 'participantOverview'}
    labels = ['Carboplatin, Pemetrexed, Amivantamab', 'Osimertinib']
    response.json.return_value = {'data': {'participantOverview': [
        {'participant_id': 'P1', 'therapy_name': labels}]}}
    app.page.on.call_args.args[1](response)
    values = options.cell_values('Therapy', 'P1', ', '.join(labels))
    assert values == labels
    assert SortRule().key(values, 'asc') == labels[0]
    assert SortRule().key(values, 'desc') == labels[1]
    with pytest.raises(AssertionError, match='displayed labels differ'):
        options.cell_values('Therapy', 'P1', 'Carboplatin, Osimertinib')


def test_ctdc_csv_rejects_missing_labels_inside_quoted_regimens():
    helper = APPS['CTDC'].RESULT_TABS_CLASS(Mock())
    headers = ['Participant ID', 'Therapy', 'Therapy Category', 'Best Response']
    reference = Table(headers, [['P1', '["Drug A, Drug B", "Drug C"]', '["Targeted"]', '["Stable Disease"]']])
    actual = Table(headers, [['P1', 'Drug C, Drug A, Drug B', 'Targeted', 'Stable Disease']])
    expected, observed = helper.prepare_comparison('Participants', reference, actual)
    assert not any(compare_export(expected, observed, ('Participant ID',)).values())
    actual.rows[0][1] = 'Drug A, Drug C'
    expected, observed = helper.prepare_comparison('Participants', reference, actual)
    assert all(compare_export(expected, observed, ('Participant ID',)).values())
