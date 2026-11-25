"""GC CSV cases compare complete exports against parameterized Memgraph queries."""
import json
from pathlib import Path
from unittest.mock import Mock, call

import openpyxl
import pytest

from Commons.apps.gc.app import GC
from Commons.apps.gc.result_tabs import GCResultTabs
from Commons.db_source import Table
from Commons.excel_testcase.runner import run_testcase_excel
from Commons.query_reader import read_query_file
from Commons.result_tabs import compare_export

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('tab', ['Participants', 'Samples', 'Files'])
def test_gc_csv_cases_load_shared_queries_and_dispatch_download_verification(tab):
    case = ROOT / f'Testcases/GC/result_tabs/{tab.lower()}/TC01_GC_Verify_{tab}_Tab_CSV_Download.xlsx'
    app = Mock(spec=GC)
    run_testcase_excel(app, case)
    app.load_query_file.assert_called_once_with('GC_ResultTabDownloads.xlsx')
    app.select_filter.assert_has_calls([
        call('StudyFacet/PHS_Accession', 'phs000720'), call('FilesFacet/FileType', 'hdf5')])
    app.result_tabs.download.assert_called_once_with(tab, 'CSV', case.name)
    app.result_tabs.verify_download.assert_called_once_with(tab, 'CSV')
    app.assert_no_failures.assert_called_once_with()
    workbook = openpyxl.load_workbook(case)
    assert workbook['_Lists'].sheet_state == 'hidden'
    assert workbook['Steps'].sheet_view.showGridLines
    validation = workbook['Steps'].data_validations.dataValidation[0]
    assert validation.formula1 in workbook.defined_names
    workbook.close()


def test_gc_query_workbook_has_parameterized_full_exports_and_independent_counts():
    query = read_query_file('GC', 'GC_ResultTabDownloads.xlsx')
    assert query.parameters == {'study': 'phs000720', 'file_type': 'HDF5', 'limit': 100000}
    assert len(query.queries_by_tab) == 6
    for spec in GCResultTabs.EXPORTS.values():
        for key in (spec.query_tab, spec.count_query_tab):
            text = query.query_for_tab(key)
            assert all(parameter in text for parameter in ('$study', '$file_type', '$limit'))
            assert 'phs000720' not in text and 'HDF5' not in text
        assert 'count(DISTINCT ' in query.query_for_tab(spec.count_query_tab)


def participant_tables():
    headers = list(GCResultTabs.EXPORTS['Participants'].headers)
    expected = Table(headers, [[
        'P1', json.dumps(['Study, with comma']), json.dumps(['phs000720']), 'Female',
        json.dumps(['S1', 'S2']), '', '', json.dumps(['Neoplasm, benign', 'Other'])]])
    actual = Table(headers, [[
        'P1', 'Study, with comma', 'phs000720', 'Female', 'S2,S1', '', '', 'Other,Neoplasm, benign']])
    return expected, actual


def test_gc_export_arrays_preserve_labels_with_embedded_commas():
    helper = GCResultTabs(None)
    expected, actual = helper.prepare_comparison('Participants', *participant_tables())
    assert not any(compare_export(expected, actual, helper.EXPORTS['Participants'].identity_columns).values())


@pytest.mark.parametrize('column,value', [
    ('Samples', 'S1,S1'), ('Samples', 'S1,S3'),
    ('Primary Diagnosis', 'Neoplasm, Other,benign'),
])
def test_gc_export_arrays_reject_replaced_records_duplicates_and_broken_labels(column, value):
    helper = GCResultTabs(None)
    expected, actual = participant_tables()
    actual.rows[0][actual.header.index(column)] = value
    expected, actual = helper.prepare_comparison('Participants', expected, actual)
    assert all(compare_export(expected, actual, helper.EXPORTS['Participants'].identity_columns).values())
