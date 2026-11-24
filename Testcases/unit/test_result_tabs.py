"""Result-tab exports must match independent data without row-limit truncation."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc.app import C3DC
from Commons.apps.c3dc.result_tabs import C3DCResultTabs, category_text_matches
from Commons.db_source import Table, MemgraphSource
from Commons.excel_testcase.registry import get_profile
from Commons.excel_testcase.runner import run_testcase_excel
from Commons.object_repository import ObjectRepository
from Commons.query_reader import QueryFile, read_query_file
from Commons.result_tabs import compare_export, read_csv_export

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / 'Testcases/C3DC/result_tabs/participants/TC01_C3DC_Verify_Participants_Tab_CSV_Download.xlsx'


def test_csv_parser_preserves_quoted_labels_bom_and_identifiers(tmp_path):
    path = tmp_path / 'result.csv'
    path.write_text('\ufeffID,Diagnosis\n"00123","Neoplasm, benign"\n\n', encoding='utf-8')
    assert read_csv_export(path) == Table(['ID', 'Diagnosis'], [['00123', 'Neoplasm, benign']])


@pytest.mark.parametrize('body', ['ID,ID\na,a\n', 'ID,Sex\na\n', ''])
def test_csv_parser_rejects_broken_schema(tmp_path, body):
    path = tmp_path / 'result.csv'
    path.write_text(body)
    with pytest.raises(AssertionError):
        read_csv_export(path)


def test_export_comparison_detects_wrong_membership_and_values_at_same_count():
    expected = Table(['ID', 'Sex'], [['a', 'Female'], ['b', 'Male']])
    assert not any(compare_export(expected, Table(expected.header, expected.rows[::-1]), ('ID',)).values())
    for rows in [[['a', 'Male'], ['b', 'Male']], [['a', 'Female'], ['c', 'Male']]]:
        assert all(compare_export(expected, Table(expected.header, rows), ('ID',)).values())
    with pytest.raises(AssertionError, match='duplicate identities'):
        compare_export(expected, Table(expected.header, [['a', 'Female'], ['a', 'Female']]), ('ID',))


@pytest.mark.parametrize('text,values,passes', [
    ('Other, Soft Tissue Tumors', ['Soft Tissue Tumors', 'Other'], True),
    ('Other, Leukemias, NOS', ['Leukemias, NOS', 'Other'], True),
    ('A, B, C', ['A, B', 'C'], True),
    ('A, B, C', ['A, C', 'B'], False),
    ('Other, Other', ['Other'], False),
    ('Other', ['Other', 'Other'], False),
])
def test_category_comparison_preserves_whole_labels_and_multiplicity(text, values, passes):
    assert category_text_matches(text, values) is passes


def test_expected_export_query_bypasses_display_limits_and_rejects_truncation():
    app = Mock(query_file=QueryFile(Path('queries.xlsx')))
    helper = C3DCResultTabs(app)
    headers = list(helper.EXPORTS['Participants'].headers)
    app.source.fetch_tab_table.side_effect = [Table(headers, [['value'] * len(headers)]), Table(['total'], [['2']])]
    with pytest.raises(AssertionError, match='incomplete: 1 of 2'):
        helper.expected_table('Participants')
    assert all(call.kwargs['apply_row_limit'] is False for call in app.source.fetch_tab_table.call_args_list)


def test_query_workbook_parameters_are_passed_to_bolt_without_interpolation():
    query = read_query_file('C3DC', 'C3DC_ResultTabDownloads.xlsx')
    assert query.parameters == {'diagnosis': 'Abdominal fibromatosis', 'limit': 100000}
    for tab in ('ParticipantsExportTab', 'ParticipantsExportCount'):
        cypher = query.query_for_tab(tab)
        assert '$diagnosis' in cypher
        assert '$study' not in cypher
        assert ':study' not in cypher
    source = MemgraphSource('bolt://localhost:7687', 'user', 'password')
    source.run_cypher_as_table = Mock(return_value=Table())
    source.fetch_tab_table(query, 'ParticipantsExportTab', apply_row_limit=False)
    assert source.run_cypher_as_table.call_args.kwargs['parameters'] == query.parameters


@pytest.mark.parametrize('tab,case,table_id', [
    ('Participants', CASE, 'participant_tab_table'),
    ('Studies', ROOT / 'Testcases/C3DC/result_tabs/studies/TC01_C3DC_Verify_Studies_Tab_CSV_Download.xlsx', 'study_tab_table'),
    ('Samples', ROOT / 'Testcases/C3DC/result_tabs/samples/TC01_C3DC_Verify_Samples_Tab_CSV_Download.xlsx', 'sample_tab_table'),
    ('GeneticAnalysis', ROOT / 'Testcases/C3DC/result_tabs/genetic_analysis/TC01_C3DC_Verify_Genetic_Analysis_Tab_CSV_Download.xlsx', 'genetic_analysis_tab_table'),
    ('Files', ROOT / 'Testcases/C3DC/result_tabs/files/TC01_C3DC_Verify_Files_Tab_CSV_Download.xlsx', 'file_tab_table'),
    ('ImagingData', ROOT / 'Testcases/C3DC/result_tabs/imaging_data/TC01_C3DC_Verify_Imaging_Data_Tab_CSV_Download.xlsx', 'imaging_data_tab_table'),
])
def test_result_tab_case_dispatches_filters_download_and_verification(tab, case, table_id):
    import openpyxl
    with case.open('rb') as stream:
        workbook = openpyxl.load_workbook(stream)
        assert workbook['_Lists'].sheet_state == 'hidden'
        validation = workbook['Steps'].data_validations.dataValidation[0]
        assert validation.formula1 in workbook.defined_names
        workbook.close()
    app = Mock(spec=C3DC)
    run_testcase_excel(app, case)
    app.select_filter.assert_called_once_with('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    app.open_explore.assert_called_once_with()
    if tab in ('Files', 'ImagingData'):
        app.open_explore_files.assert_called_once_with()
        assert app.mock_calls.index(next(c for c in app.mock_calls if c[0] == 'select_filter')) < app.mock_calls.index(next(c for c in app.mock_calls if c[0] == 'open_explore_files'))
    app.result_tabs.download.assert_called_once_with(tab, 'CSV', case.name)
    app.result_tabs.verify_download.assert_called_once_with(tab, 'CSV')
    assert 'result_tabs' in get_profile('C3DC').case_subdirs
    import yaml
    assert 'result_tabs/**/TC*.xlsx' in yaml.safe_load((ROOT / 'Config/suites.yaml').read_text())['C3DC']['regression']
    repo = ObjectRepository('C3DC')
    assert table_id in repo.xpath(f'{tab}ResultTab/CSV')


def test_result_tab_adapter_instances_do_not_share_download_state():
    first, second = C3DC.__new__(C3DC), C3DC.__new__(C3DC)
    first.result_tabs.downloads[('Participants', 'CSV')] = Path('one.csv')
    assert not second.result_tabs.downloads


def test_duplicate_toolbars_download_only_the_active_table_csv(page, tmp_path):
    from Commons.browser_actions import Ui
    page.set_content('''<div id="participant_tab_table">
      <button title="Download filtered results" onclick="document.querySelector('#dropdownListItemCSV').hidden=false">Download</button>
      <a id="dropdownListItemCSV" hidden download="CCDI Participants Download 2026-11-24 09-00-00.csv" href="data:text/csv,ID%0Aa">CSV</a>
      <button title="Download filtered results">Download</button>
      <a id="dropdownListItemCSV" hidden>CSV</a></div>''')
    app = Mock(page=page, ui=Ui(page), repo=ObjectRepository('C3DC'), output_dir=tmp_path, results=[])
    helper = C3DCResultTabs(app)
    path = helper.download('Participants', 'CSV', 'example.xlsx')
    assert path.read_text() == 'ID\na'
    assert helper.downloads[('Participants', 'CSV')] == path


def test_studies_export_list_comparison_preserves_full_values_and_counts():
    import json
    helper = C3DCResultTabs(None)
    headers = list(helper.EXPORTS['Studies'].headers)
    row = ['Study', 'phs001', 'Active', json.dumps(['Tumor, NOS (2)', 'Other (1)']),
           '[]', '3', '0', '0', '[]', '[]', json.dumps(['Smith, MD']), '[]']
    actual = ['Study', 'phs001', 'Active', 'Other (1), Tumor, NOS (2)',
              '', '3', '0', '0', '', '', 'Smith, MD', '']
    def differences(values):
        expected, exported = helper.prepare_comparison('Studies', Table(headers, [row]), Table(headers, [values]))
        return compare_export(expected, exported, ('Study ID',))
    assert not any(differences(actual).values())
    for wrong in ['Tumor, NOS (2)', 'Other (2), Tumor, NOS (2)']:
        bad = actual.copy()
        bad[3] = wrong
        assert all(differences(bad).values())


def test_imaging_export_compares_each_series_within_the_same_study():
    import json
    helper = C3DCResultTabs(None)
    headers = list(helper.EXPORTS['ImagingData'].headers)
    rows = [['study', series, 'phs001', json.dumps([participant]), json.dumps([sample]),
             'https://viewer/' + series, 'Slide Microscopy', 'H&E', 'FFPE', '40X']
            for series, participant, sample in [('series1', 'p1', 's1'), ('series2', 'p2', 's2')]]
    actual = [list(row) for row in rows]
    for row in actual:
        row[3], row[4] = json.loads(row[3])[0], json.loads(row[4])[0]
    expected, exported = helper.prepare_comparison('ImagingData', Table(headers, rows), Table(headers, actual))
    assert not any(compare_export(expected, exported, ('Study UID', 'Series UID')).values())
    actual[0][4] = 'wrong-sample'
    expected, exported = helper.prepare_comparison('ImagingData', Table(headers, rows), Table(headers, actual))
    assert all(compare_export(expected, exported, ('Study UID', 'Series UID')).values())
