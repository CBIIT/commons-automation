"""Result-tab exports must match independent data without row-limit truncation."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc.app import C3DC
from Commons.apps.c3dc.result_tabs import C3DCResultTabs, category_text_matches, canonical_participant_json, canonical_result_json, JSON_RECORD_SCHEMAS
from Commons.db_source import Table, MemgraphSource
from Commons.excel_testcase.registry import get_profile
from Commons.excel_testcase.runner import run_testcase_excel
from Commons.object_repository import ObjectRepository
from Commons.query_reader import QueryFile, read_query_file
from Commons.result_tabs import compare_export, read_csv_export, read_json_records

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


@pytest.mark.parametrize('tab,case,table_id,fmt', [
    ('Participants', CASE, 'participant_tab_table', 'CSV'),
    ('Studies', ROOT / 'Testcases/C3DC/result_tabs/studies/TC01_C3DC_Verify_Studies_Tab_CSV_Download.xlsx', 'study_tab_table', 'CSV'),
    ('Samples', ROOT / 'Testcases/C3DC/result_tabs/samples/TC01_C3DC_Verify_Samples_Tab_CSV_Download.xlsx', 'sample_tab_table', 'CSV'),
    ('GeneticAnalysis', ROOT / 'Testcases/C3DC/result_tabs/genetic_analysis/TC01_C3DC_Verify_Genetic_Analysis_Tab_CSV_Download.xlsx', 'genetic_analysis_tab_table', 'CSV'),
    ('Files', ROOT / 'Testcases/C3DC/result_tabs/files/TC01_C3DC_Verify_Files_Tab_CSV_Download.xlsx', 'file_tab_table', 'CSV'),
    ('ImagingData', ROOT / 'Testcases/C3DC/result_tabs/imaging_data/TC01_C3DC_Verify_Imaging_Data_Tab_CSV_Download.xlsx', 'imaging_data_tab_table', 'CSV'),
    ('Participants', CASE.with_name('TC02_C3DC_Verify_Participants_Tab_JSON_Download.xlsx'), 'participant_tab_table', 'JSON'),
    ('Studies', ROOT / 'Testcases/C3DC/result_tabs/studies/TC02_C3DC_Verify_Studies_Tab_JSON_Download.xlsx', 'study_tab_table', 'JSON'),
    ('Samples', ROOT / 'Testcases/C3DC/result_tabs/samples/TC02_C3DC_Verify_Samples_Tab_JSON_Download.xlsx', 'sample_tab_table', 'JSON'),
    ('GeneticAnalysis', ROOT / 'Testcases/C3DC/result_tabs/genetic_analysis/TC02_C3DC_Verify_Genetic_Analysis_Tab_JSON_Download.xlsx', 'genetic_analysis_tab_table', 'JSON'),
    ('Files', ROOT / 'Testcases/C3DC/result_tabs/files/TC02_C3DC_Verify_Files_Tab_JSON_Download.xlsx', 'file_tab_table', 'JSON'),
    ('ImagingData', ROOT / 'Testcases/C3DC/result_tabs/imaging_data/TC02_C3DC_Verify_Imaging_Data_Tab_JSON_Download.xlsx', 'imaging_data_tab_table', 'JSON'),
])
def test_result_tab_case_dispatches_filters_download_and_verification(tab, case, table_id, fmt):
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
    app.result_tabs.download.assert_called_once_with(tab, fmt, case.name)
    app.result_tabs.verify_download.assert_called_once_with(tab, fmt)
    assert 'result_tabs' in get_profile('C3DC').case_subdirs
    import yaml
    assert 'result_tabs/**/TC*.xlsx' in yaml.safe_load((ROOT / 'Config/suites.yaml').read_text())['C3DC']['regression']
    repo = ObjectRepository('C3DC')
    assert table_id in repo.xpath(f'{tab}ResultTab/{fmt}')


def test_result_tab_adapter_instances_do_not_share_download_state():
    first, second = C3DC.__new__(C3DC), C3DC.__new__(C3DC)
    first.result_tabs.downloads[('Participants', 'CSV')] = Path('one.csv')
    assert not second.result_tabs.downloads


@pytest.mark.parametrize('fmt,extension', [('CSV', 'csv'), ('JSON', 'json'), ('JSON', 'csv')])
def test_duplicate_toolbars_download_only_the_active_table_format(page, tmp_path, fmt, extension):
    from Commons.browser_actions import Ui
    page.set_content(f'''<div id="participant_tab_table">
      <button title="Download filtered results" onclick="document.querySelector('#dropdownListItem{fmt}').hidden=false">Download</button>
      <a id="dropdownListItem{fmt}" hidden download="CCDI Participants Download 2026-11-24 09-00-00.{extension}" href="data:text/plain,ID%0Aa">{fmt}</a>
      <button title="Download filtered results">Download</button>
      <a id="dropdownListItem{fmt}" hidden>{fmt}</a></div>''')
    app = Mock(page=page, ui=Ui(page), repo=ObjectRepository('C3DC'), output_dir=tmp_path, results=[])
    helper = C3DCResultTabs(app)
    if extension != fmt.lower():
        with pytest.raises(AssertionError, match='Unexpected export filename'):
            helper.download('Participants', fmt, 'example.xlsx')
        return
    path = helper.download('Participants', fmt, 'example.xlsx')
    assert path.read_text() == 'ID\na'
    assert helper.downloads[('Participants', fmt)] == path


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


@pytest.mark.parametrize('body', [
    '{}', '[1]', '[{"id":"one","id":"two"}]',
    '[{"nested":{"id":"one","id":"two"}}]', '[{"age":NaN}]',
])
def test_json_parser_rejects_invalid_structure_duplicate_keys_and_numbers(tmp_path, body):
    path = tmp_path / 'download.json'
    path.write_text(body)
    with pytest.raises(AssertionError):
        read_json_records(path)


def participant_json_fixture():
    return {
        '__typename': 'ParticipantOverViewResult', 'id': 'guid1', 'Participant ID': 'p1',
        'Sex at Birth': 'Female', 'Diagnosis': ['First', 'Second'],
        'Diagnosis Category': ['Neoplasms, NOS', 'Other'],
        'Age at Diagnosis (days)': '1; 2', 'Anatomic Site': ['blood', 'blood'],
        'Last Known Survival Status': None, 'Age at Last Known Survival Status': None,
        'Treatment Type': ['Surgery', 'Surgery'], 'Age at Treatment Start': '1; 2',
        'Available CPI Mapping': [{
            '__typename': 'CPIOverViewResult', 'associated_id': 'subject1',
            'repository_of_synonym_id': 'dbgap_subject_id', 'domain_description': 'Subject ID',
            'domain_category': 'organizational_identifier', 'data_location': 'https://example.org/',
            'data_type': 'external', 'p_id': None,
        }],
    }


def test_json_comparison_preserves_types_duplicates_and_ordered_clinical_values():
    import copy
    record = participant_json_fixture()
    reordered = copy.deepcopy(record)
    reordered['Diagnosis Category'].reverse()
    assert canonical_participant_json(record) == canonical_participant_json(reordered)
    for key, value in [('Last Known Survival Status', ''), ('Treatment Type', ['Surgery']),
                       ('Diagnosis', ['Second', 'First'])]:
        changed = copy.deepcopy(record)
        changed[key] = value
        assert canonical_participant_json(record) != canonical_participant_json(changed)
    for key, value in [('Diagnosis', 'First, Second'), ('id', 1), ('Unknown', 'value')]:
        changed = copy.deepcopy(record)
        changed[key] = value
        with pytest.raises(AssertionError):
            canonical_participant_json(changed)


def test_json_reference_combines_database_records_and_exact_cpi_api_values(tmp_path):
    import copy
    import json
    record = participant_json_fixture()
    database = copy.deepcopy(record)
    del database['Available CPI Mapping']
    app = Mock(query_file=read_query_file('C3DC', 'C3DC_ResultTabDownloads.xlsx'))
    app.settings.url = 'https://example.org/'
    app.ui.timeout_ms = 30000
    app.source.fetch_tab_table.side_effect = [
        Table(['Participant ID', 'record'], [['p1', json.dumps(database)]]), Table(['total'], [['1']])]
    response = app.page.request.post.return_value
    response.ok = True
    response.json.return_value = {'data': {'participantOverview': [
        {'participant_id': 'p1', 'cpi_data': record['Available CPI Mapping']}]}}
    helper = C3DCResultTabs(app)
    expected = helper.expected_table('Participants', 'JSON')
    assert app.source.fetch_tab_table.call_args_list[0].args[1] == 'ParticipantsJSONExportTab'
    assert app.source.fetch_tab_table.call_args_list[1].args[1] == 'ParticipantsExportCount'
    assert app.page.request.post.call_args.kwargs['data']['variables'] == {'ids': ['p1'], 'first': 1}
    path = tmp_path / 'download.json'
    path.write_text(json.dumps([record]))
    actual = helper.read_export('Participants', 'JSON', path)
    assert not any(compare_export(expected, actual, ('Participant ID',)).values())
    record['Available CPI Mapping'][0]['data_location'] = 'https://wrong.example.org/'
    path.write_text(json.dumps([record]))
    actual = helper.read_export('Participants', 'JSON', path)
    assert all(compare_export(expected, actual, ('Participant ID',)).values())


def file_json_fixture():
    return {
        '__typename': 'FileOverViewResult', 'id': 'guid1', 'file_id': 'guid1',
        'File Name': 'a.bam', 'Data Category': ['Sequencing'], 'File Type': 'bam',
        'Study ID': 'phs001', 'Participant ID': ['p1', 'p2'], 'Sample ID': ['s1', 's2'],
        'Anatomic Site': ['blood'], 'Age at Collection': '2; 1; 1',
        'Sample Tumor Status': ['Tumor'], 'Tumor Spatial Extent': ['Local'],
    }


def test_file_json_preserves_nulls_and_duplicates_and_requires_database_name_alias():
    import copy
    import json
    record = file_json_fixture()
    reordered = copy.deepcopy(record)
    reordered['Participant ID'].reverse()
    reordered['Age at Collection'] = '1; 2; 1'
    assert canonical_result_json('Files', record) == canonical_result_json('Files', reordered)
    reordered['Age at Collection'] = '1; 2'
    assert canonical_result_json('Files', record) != canonical_result_json('Files', reordered)
    missing = copy.deepcopy(record)
    missing['Sample ID'] = None
    empty = copy.deepcopy(missing)
    empty['Sample ID'] = []
    assert canonical_result_json('Files', missing) != canonical_result_json('Files', empty)
    database = copy.deepcopy(record)
    database['File Name'] = ['a.bam', 'alias.bam']
    record['File Name'] = 'alias.bam'
    helper = C3DCResultTabs(None)
    def differences(actual):
        expected = Table(['id', 'record'], [['guid1', json.dumps(database)]])
        actual = Table(['id', 'record'], [['guid1', canonical_result_json('Files', actual)]])
        expected, actual = helper.prepare_comparison('Files', expected, actual, 'JSON')
        return compare_export(expected, actual, ('id',))
    assert not any(differences(record).values())
    record['File Name'] = 'not-in-database.bam'
    assert all(differences(record).values())


def test_study_json_checks_every_ranked_item_beyond_top_five():
    record = {
        '__typename': 'StudyOverViewResult', 'id': 'study-guid', 'Study ID': 'phs001',
        'PubMed ID': [], 'Grant ID': [], 'Manifest': 'phs001', 'Study Name': 'Study',
        'Study Phase': 'Active', 'Principal Investigator(s)': ['Smith, MD'],
        'Diagnosis (Top 5)': ['Tumor, NOS (' + str(i) + ')' for i in range(1, 8)],
        'Diagnosis Anatomic Site (Top 5)': ['blood (7)'], 'Number of Participants': '7',
        'Number of Samples': '0', 'Number of Files': '0', 'File Type (Top 5)': [],
    }
    complete = canonical_result_json('Studies', record)
    record['Diagnosis (Top 5)'].reverse()
    assert canonical_result_json('Studies', record) == complete
    record['Diagnosis (Top 5)'] = record['Diagnosis (Top 5)'][:5]
    assert canonical_result_json('Studies', record) != complete
    record['Number of Participants'] = 7
    with pytest.raises(AssertionError):
        canonical_result_json('Studies', record)


@pytest.mark.parametrize('tab', JSON_RECORD_SCHEMAS)
def test_other_json_tabs_use_database_records_without_cpi_api(tab):
    import json
    schema = JSON_RECORD_SCHEMAS[tab]
    record = {key: [] if key in schema['arrays'] else 'value' for key in schema['fields']}
    record['__typename'] = schema['typename']
    record['id'] = 'guid1'
    if tab == 'Files':
        record['File Name'] = ['allowed.bam']
    app = Mock(query_file=read_query_file('C3DC', 'C3DC_ResultTabDownloads.xlsx'))
    app.source.fetch_tab_table.side_effect = [
        Table(['id', 'record'], [['guid1', json.dumps(record)]]), Table(['total'], [['1']])]
    result = C3DCResultTabs(app).expected_table(tab, 'JSON')
    assert result.header == ['id', 'record'] and len(result.rows) == 1
    assert app.source.fetch_tab_table.call_args_list[0].args[1] == tab + 'JSONExportTab'
    assert app.source.fetch_tab_table.call_args_list[1].args[1] == tab + 'ExportCount'
    app.page.request.post.assert_not_called()
