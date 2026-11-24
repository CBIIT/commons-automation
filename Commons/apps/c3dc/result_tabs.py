"""C3DC result-tab controls and export specifications."""
import json
from functools import lru_cache

from playwright.sync_api import expect

from Commons.db_source import Table
from Commons.result_tabs import ResultTabs, ResultTabExportSpec


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

    # -----------------------------------------------------------------------
    # Download menu: repeated above and below the active result table
    # -----------------------------------------------------------------------
    def download_trigger(self, tab, fmt):
        spec = self.EXPORTS[tab]
        self.app.ui.visible(self.app.repo.xpath(spec.download_key)).first.click()
        option = self.app.ui.visible(self.app.repo.xpath(spec.format_keys[fmt])).first
        expect(option).to_be_visible(timeout=self.app.ui.timeout_ms)
        return option

    # -----------------------------------------------------------------------
    # Export arrays: order is unspecified; labels can contain commas
    # -----------------------------------------------------------------------
    def prepare_comparison(self, tab, expected, actual):
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
