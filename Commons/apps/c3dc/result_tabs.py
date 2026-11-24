"""C3DC result-tab controls and export specifications."""
import json
from functools import lru_cache

from playwright.sync_api import expect

from Commons.db_source import Table
from Commons.result_tabs import ResultTabs, ResultTabExportSpec, read_json_records


PARTICIPANT_JSON_FIELDS = (
    '__typename', 'id', 'Participant ID', 'Sex at Birth', 'Diagnosis', 'Diagnosis Category',
    'Age at Diagnosis (days)', 'Anatomic Site', 'Last Known Survival Status',
    'Age at Last Known Survival Status', 'Treatment Type', 'Age at Treatment Start',
    'Available CPI Mapping',
)
CPI_FIELDS = ('__typename', 'associated_id', 'repository_of_synonym_id', 'domain_description',
              'domain_category', 'data_location', 'data_type', 'p_id')


# JSON export fields, array types, and nullable values.
JSON_RECORD_SCHEMAS = {
    'Studies': {
        'typename': 'StudyOverViewResult',
        'fields': ('__typename', 'id', 'Study ID', 'PubMed ID', 'Grant ID', 'Manifest',
                   'Study Name', 'Study Phase', 'Principal Investigator(s)',
                   'Diagnosis (Top 5)', 'Diagnosis Anatomic Site (Top 5)',
                   'Number of Participants', 'Number of Samples', 'Number of Files',
                   'File Type (Top 5)'),
        'arrays': ('PubMed ID', 'Grant ID', 'Principal Investigator(s)', 'Diagnosis (Top 5)',
                   'Diagnosis Anatomic Site (Top 5)', 'File Type (Top 5)'),
        'nullable': ('Study Name', 'Study Phase'),
    },
    'Samples': {
        'typename': 'SampleOverViewResult',
        'fields': ('__typename', 'id', 'Participant ID', 'Sample ID', 'Study ID',
                   'Tumor Spatial Extent', 'Anatomic Site',
                   'Participant Age at Collection (days)', 'Sample Tumor Status'),
        'arrays': (),
        'nullable': ('Tumor Spatial Extent', 'Sample Tumor Status'),
    },
    'GeneticAnalysis': {
        'typename': 'GeneticAnalysisOverviewResult',
        'fields': ('__typename', 'dbgap_accession', 'Participant ID', 'Study ID', 'id',
                   'Genetic Analysis ID', 'Alteration', 'Gene Symbol (Top 5)', 'HGVS Genome',
                   'Status', 'Reported Significance', 'Reported Significance System'),
        'arrays': ('Gene Symbol (Top 5)',),
        'nullable': ('Alteration', 'HGVS Genome', 'Status', 'Reported Significance',
                     'Reported Significance System'),
    },
    'Files': {
        'typename': 'FileOverViewResult',
        'fields': ('__typename', 'id', 'File Name', 'Data Category', 'File Type', 'Study ID',
                   'Participant ID', 'Sample ID', 'file_id', 'Anatomic Site',
                   'Age at Collection', 'Sample Tumor Status', 'Tumor Spatial Extent'),
        'arrays': ('Data Category', 'Participant ID', 'Sample ID', 'Anatomic Site',
                   'Sample Tumor Status', 'Tumor Spatial Extent'),
        'nullable': ('Sample ID', 'Anatomic Site', 'Age at Collection', 'Sample Tumor Status',
                     'Tumor Spatial Extent'),
    },
    'ImagingData': {
        'typename': 'IDCOverviewResult',
        'fields': ('__typename', 'id', 'IDC Histopathology Viewer', 'Study UID', 'Series UID',
                   'Study ID', 'Participant ID', 'Sample ID', 'Image Modality', 'Magnification',
                   'Fixation/Embedding Method', 'Staining Method'),
        'arrays': ('Participant ID', 'Sample ID'),
        'nullable': ('Image Modality', 'Magnification', 'Fixation/Embedding Method',
                     'Staining Method'),
    },
}


def canonical_participant_json(record):
    """Preserve JSON types and ordered clinical arrays; sort only unordered mappings/categories."""
    assert isinstance(record, dict) and set(record) == set(PARTICIPANT_JSON_FIELDS), \
        'Participants JSON fields differ from the export schema'
    arrays = ('Diagnosis', 'Diagnosis Category', 'Anatomic Site', 'Treatment Type')
    nullable = ('Sex at Birth', 'Last Known Survival Status', 'Age at Last Known Survival Status')
    for key in PARTICIPANT_JSON_FIELDS:
        value = record[key]
        if key in arrays:
            assert isinstance(value, list) and all(isinstance(x, str) for x in value), \
                f'{key} must be an array of strings'
        elif key != 'Available CPI Mapping':
            assert isinstance(value, str) or (key in nullable and value is None), \
                f'{key} has an invalid JSON type'
    assert record['__typename'] == 'ParticipantOverViewResult', 'Unexpected participant JSON type'
    assert record['id'] and record['Participant ID'], 'Participants JSON has an empty identity'
    mappings = record['Available CPI Mapping']
    assert isinstance(mappings, list), 'CPI mappings must be an array'
    for mapping in mappings:
        assert isinstance(mapping, dict) and set(mapping) == set(CPI_FIELDS), 'CPI mapping fields differ'
        assert mapping['__typename'] == 'CPIOverViewResult', 'Unexpected CPI JSON type'
        assert all(isinstance(mapping[key], str) or (key == 'p_id' and mapping[key] is None)
                   for key in CPI_FIELDS), 'CPI mapping has an invalid JSON type'
    normalized = dict(record)
    normalized['Diagnosis Category'] = sorted(record['Diagnosis Category'])
    normalized['Available CPI Mapping'] = sorted(mappings, key=lambda item: json.dumps(item, sort_keys=True))
    return json.dumps(normalized, sort_keys=True, ensure_ascii=False)


def canonical_result_json(tab, record):
    """Validate every field and preserve JSON types; unordered metadata arrays keep duplicates."""
    if tab == 'Participants':
        return canonical_participant_json(record)
    schema = JSON_RECORD_SCHEMAS[tab]
    assert isinstance(record, dict) and set(record) == set(schema['fields']), \
        f'{tab} JSON fields differ from the export schema'
    assert record['__typename'] == schema['typename'], f'Unexpected {tab} JSON type'
    assert isinstance(record['id'], str) and record['id'], f'{tab} JSON has an empty identity'
    normalized = dict(record)
    for key, value in record.items():
        if value is None and key in schema['nullable']:
            continue
        if key in schema['arrays']:
            assert isinstance(value, list) and all(isinstance(item, str) for item in value), \
                f'{tab} {key} must be an array of strings'
            normalized[key] = sorted(value)
        else:
            assert isinstance(value, str), f'{tab} {key} has an invalid JSON type'
    if tab == 'Files' and record['Age at Collection'] is not None:
        normalized['Age at Collection'] = '; '.join(sorted(record['Age at Collection'].split('; ')))
    return json.dumps(normalized, sort_keys=True, ensure_ascii=False)


def category_text_matches(text, categories):
    """Compare an unordered flattened list without splitting commas inside labels."""
    @lru_cache(None)
    def consume(remaining_text, remaining_values):
        if not remaining_values:
            return remaining_text == ''
        for index, value in enumerate(remaining_values):
            suffix = ', ' if len(remaining_values) > 1 else ''
            prefix = value + suffix
            if remaining_text.startswith(prefix) and consume(
                    remaining_text[len(prefix):], remaining_values[:index] + remaining_values[index + 1:]):
                return True
        return False
    return consume(text.strip(), tuple(sorted(categories)))


class C3DCResultTabs(ResultTabs):
    # -----------------------------------------------------------------------
    # Export schemas and independent query names
    # -----------------------------------------------------------------------
    EXPORTS = {
        'Participants': ResultTabExportSpec(
            table_key='ResultTabs/Participants-Tbl',
            download_key='ParticipantsResultTab/Download',
            format_keys={'CSV': 'ParticipantsResultTab/CSV'},
            headers=('Participant ID', 'Sex at Birth', 'Diagnosis', 'Diagnosis Category',
                     'Age at Diagnosis (days)', 'Anatomic Site', 'Last Known Survival Status',
                     'Age at Last Known Survival Status', 'Treatment Type', 'Age at Treatment Start'),
            identity_columns=('Participant ID',),
            query_tab='ParticipantsExportTab', count_query_tab='ParticipantsExportCount',
            filename_pattern=r'CCDI Participants Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.csv',
        ),
        'Studies': ResultTabExportSpec(
            table_key='ResultTabs/Studies-Tbl',
            download_key='StudiesResultTab/Download',
            format_keys={'CSV': 'StudiesResultTab/CSV'},
            headers=('Study Name', 'Study ID', 'Study Phase', 'Diagnosis',
                     'Diagnosis Anatomic Site', 'Number of Participants', 'Number of Samples',
                     'Number of Files', 'File Type', 'PubMed ID', 'Principal Investigator(s)', 'Grant ID'),
            identity_columns=('Study ID',),
            query_tab='StudiesExportTab', count_query_tab='StudiesExportCount',
            filename_pattern=r'CCDI Studies Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.csv',
        ),
        'Samples': ResultTabExportSpec(
            table_key='ResultTabs/Samples-Tbl',
            download_key='SamplesResultTab/Download',
            format_keys={'CSV': 'SamplesResultTab/CSV'},
            headers=('Participant ID', 'Sample ID', 'Study ID', 'Tumor Spatial Extent',
                     'Anatomic Site', 'Participant Age at Collection (days)', 'Sample Tumor Status'),
            identity_columns=('Sample ID',),
            query_tab='SamplesExportTab', count_query_tab='SamplesExportCount',
            filename_pattern=r'CCDI Samples Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.csv',
        ),
        'GeneticAnalysis': ResultTabExportSpec(
            table_key='ResultTabs/GeneticAnalysis-Tbl',
            download_key='GeneticAnalysisResultTab/Download',
            format_keys={'CSV': 'GeneticAnalysisResultTab/CSV'},
            headers=('Participant ID', 'Genetic Analysis ID', 'Gene Symbol', 'Status',
                     'Reported Significance', 'Reported Significance System', 'HGVS Genome',
                     'Alteration', 'Study ID'),
            identity_columns=('Genetic Analysis ID',),
            query_tab='GeneticAnalysisExportTab', count_query_tab='GeneticAnalysisExportCount',
            filename_pattern=r'CCDI Genetic Analyses Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.csv',
        ),
        'Files': ResultTabExportSpec(
            table_key='ResultTabs/Files-Tbl',
            download_key='FilesResultTab/Download',
            format_keys={'CSV': 'FilesResultTab/CSV'},
            headers=('File Name', 'Data Category', 'File Type', 'Study ID', 'Participant ID',
                     'Sample ID', 'Anatomic Site', 'Age at Collection', 'Sample Tumor Status',
                     'Tumor Spatial Extent'),
            identity_columns=('File Name',),
            query_tab='FilesExportTab', count_query_tab='FilesExportCount',
            filename_pattern=r'CCDI Files Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.csv',
        ),
        'ImagingData': ResultTabExportSpec(
            table_key='ResultTabs/ImagingData-Tbl',
            download_key='ImagingDataResultTab/Download',
            format_keys={'CSV': 'ImagingDataResultTab/CSV'},
            headers=('Study UID', 'Series UID', 'Study ID', 'Participant ID', 'Sample ID',
                     'IDC Histopathology Viewer', 'Image Modality', 'Staining Method',
                     'Fixation/Embedding Method', 'Magnification'),
            identity_columns=('Study UID', 'Series UID'),
            query_tab='ImagingDataExportTab', count_query_tab='ImagingDataExportCount',
            filename_pattern=r'CCDI Imaging Data Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.csv',
        ),
    }

    JSON_EXPORTS = {
        'Participants': ResultTabExportSpec(
            table_key='ResultTabs/Participants-Tbl',
            download_key='ParticipantsResultTab/Download',
            format_keys={'JSON': 'ParticipantsResultTab/JSON'},
            headers=('Participant ID', 'record'),
            identity_columns=('Participant ID',),
            query_tab='ParticipantsJSONExportTab', count_query_tab='ParticipantsExportCount',
            filename_pattern=r'CCDI Participants Download \d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\.json',
        ),
    }

    # Reuse navigation and count queries; each JSON tab has its own typed projection.
    for _tab in JSON_RECORD_SCHEMAS:
        _csv = EXPORTS[_tab]
        JSON_EXPORTS[_tab] = ResultTabExportSpec(
            table_key=_csv.table_key,
            download_key=_csv.download_key,
            format_keys={'JSON': f'{_tab}ResultTab/JSON'},
            headers=('id', 'record'), identity_columns=('id',),
            query_tab=f'{_tab}JSONExportTab', count_query_tab=_csv.count_query_tab,
            filename_pattern=_csv.filename_pattern.removesuffix('csv') + 'json',
        )
    del _tab, _csv

    def export_spec(self, tab, fmt='CSV'):
        if fmt == 'JSON':
            return self.JSON_EXPORTS[tab]
        return super().export_spec(tab, fmt)

    # -----------------------------------------------------------------------
    # Download menu: repeated above and below the active result table
    # -----------------------------------------------------------------------
    def download_trigger(self, tab, fmt):
        spec = self.export_spec(tab, fmt)
        self.app.ui.visible(self.app.repo.xpath(spec.download_key)).first.click()
        option = self.app.ui.visible(self.app.repo.xpath(spec.format_keys[fmt])).first
        expect(option).to_be_visible(timeout=self.app.ui.timeout_ms)
        return option

    # -----------------------------------------------------------------------
    # JSON records: clinical data from Memgraph; federated CPI data from its API
    # -----------------------------------------------------------------------
    def expected_table(self, tab, fmt='CSV'):
        expected = super().expected_table(tab, fmt)
        if fmt != 'JSON' or tab == 'Files':
            return expected
        if tab != 'Participants':
            return Table(expected.header, [
                [identity, canonical_result_json(tab, json.loads(text))]
                for identity, text in expected.rows])
        participants = [row[0] for row in expected.rows]
        query = '''query ParticipantExportCPI($ids: [String], $first: Int) {
          participantOverview(participant_ids: $ids, first: $first) {
            participant_id
            cpi_data {
              __typename associated_id repository_of_synonym_id domain_description
              domain_category data_location data_type p_id
            }
          }
        }'''
        response = self.app.page.request.post(
            self.app.settings.url.rstrip('/') + '/v1/graphql/',
            data={'query': query, 'variables': {'ids': participants, 'first': len(participants)}},
            timeout=self.app.ui.timeout_ms)
        assert response.ok, f'CPI reference request failed: HTTP {response.status}'
        payload = response.json()
        assert not payload.get('errors'), f'CPI reference query failed: {payload.get("errors")}'
        records = payload['data']['participantOverview']
        mappings = {record['participant_id']: record['cpi_data'] for record in records}
        assert len(records) == len(mappings) == len(participants) and set(mappings) == set(participants), \
            'CPI reference participant membership differs from Memgraph'
        rows = []
        for participant, text in expected.rows:
            record = json.loads(text)
            assert record['Participant ID'] == participant, 'Expected JSON record identity differs'
            record['Available CPI Mapping'] = mappings[participant]
            rows.append([participant, canonical_participant_json(record)])
        return Table(expected.header, rows)

    def read_export(self, tab, fmt, path):
        if fmt == 'JSON':
            return Table(list(self.export_spec(tab, fmt).headers), [
                [record.get('Participant ID' if tab == 'Participants' else 'id'),
                 canonical_result_json(tab, record)]
                for record in read_json_records(path)])
        return super().read_export(tab, fmt, path)

    # -----------------------------------------------------------------------
    # Export arrays: order is unspecified; labels can contain commas
    # -----------------------------------------------------------------------
    def prepare_comparison(self, tab, expected, actual, fmt='CSV'):
        if fmt == 'JSON':
            if tab == 'Files':
                # A shared GUID can have several valid names on its database metadata nodes.
                actual_by_id = {identity: json.loads(text) for identity, text in actual.rows}
                rows = []
                for identity, text in expected.rows:
                    record = json.loads(text)
                    names = record['File Name']
                    assert isinstance(names, list) and names and all(isinstance(n, str) for n in names), \
                        'Expected file names must contain database aliases'
                    exported_name = actual_by_id.get(identity, {}).get('File Name')
                    record['File Name'] = exported_name if exported_name in names else names[0]
                    rows.append([identity, canonical_result_json(tab, record)])
                expected = Table(expected.header, rows)
            return expected, actual
        if actual.header != expected.header:
            return expected, actual  # Let the shared schema check report the error.
        spec = self.EXPORTS[tab]
        identities = [expected.header.index(column) for column in spec.identity_columns]
        columns = {
            'Participants': ('Diagnosis Category',),
            'Studies': ('Diagnosis', 'Diagnosis Anatomic Site', 'File Type', 'PubMed ID',
                        'Principal Investigator(s)', 'Grant ID'),
            'Samples': ('Anatomic Site',),
            'GeneticAnalysis': ('Gene Symbol',),
            'Files': ('Data Category', 'Participant ID', 'Sample ID', 'Anatomic Site',
                      'Age at Collection', 'Sample Tumor Status', 'Tumor Spatial Extent'),
            'ImagingData': ('Participant ID', 'Sample ID'),
        }[tab]
        if tab == 'Files':
            from Commons.apps.c3dc.table_cells import resolve_file_name_aliases
            expected = Table(expected.header, [list(row) for row in expected.rows])
            resolve_file_name_aliases(actual, expected)
        expected_rows = [list(row) for row in expected.rows]
        actual_rows = [list(row) for row in actual.rows]
        for column in columns:
            index = expected.header.index(column)
            values_by_id = {}
            for row in expected_rows:
                values = json.loads(row[index])
                assert isinstance(values, list) and all(isinstance(x, str) for x in values)
                values_by_id[tuple(row[i].strip() for i in identities)] = values
                row[index] = json.dumps(sorted(values))
            for row in actual_rows:
                values = values_by_id.get(tuple(row[i].strip() for i in identities))
                if values is not None and category_text_matches(row[index], values):
                    row[index] = json.dumps(sorted(values))
                else:
                    row[index] = 'Unexpected values: ' + row[index]
        return Table(expected.header, expected_rows), Table(actual.header, actual_rows)
