"""GC result-tab CSV controls and complete export schemas."""
import json
from decimal import Decimal

from Commons.db_source import Table
from Commons.result_tabs import DirectCSVResultTabs, ResultTabExportSpec, category_text_matches


class GCResultTabs(DirectCSVResultTabs):
    # -----------------------------------------------------------------------
    # CSV export schemas and independent Memgraph query names
    # -----------------------------------------------------------------------
    EXPORTS = {
        'Participants': ResultTabExportSpec(
            table_key='Data_page/GC_ParticipantsTable',
            download_key='ParticipantsResultTab/CSV',
            format_keys={"CSV": 'ParticipantsResultTab/CSV'},
            headers=('Participant ID', 'Study Name', 'Study Accession', 'Sex', 'Samples', 'Race', 'Ethnicity', 'Primary Diagnosis'),
            identity_columns=('Participant ID', 'Study Accession'),
            query_tab='ParticipantsExportTab', count_query_tab='ParticipantsExportCount',
            filename_pattern='GC_participant_Download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Samples': ResultTabExportSpec(
            table_key='Data_page/GC_SamplesTable',
            download_key='SamplesResultTab/CSV',
            format_keys={"CSV": 'SamplesResultTab/CSV'},
            headers=('Study Name', 'Study Accession', 'Sample ID', 'Sample Name', 'Organization Name', 'Participant ID', 'Files', 'Sample Type', 'Sample Tumor Status', 'Organ or Tissue'),
            identity_columns=('Sample ID', 'Study Accession'),
            query_tab='SamplesExportTab', count_query_tab='SamplesExportCount',
            filename_pattern='GC_sample_Download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Files': ResultTabExportSpec(
            table_key='Data_page/GC_FilesTable',
            download_key='FilesResultTab/CSV',
            format_keys={"CSV": 'FilesResultTab/CSV'},
            headers=('Study Name', 'Study Accession', 'File Name', 'File ID', 'File Type', 'Sample ID', 'Participant ID', 'File Size', 'Study Data Type', 'Library Strategy', 'Supplementary Files', 'Image Modality'),
            identity_columns=('File ID',),
            query_tab='FilesExportTab', count_query_tab='FilesExportCount',
            filename_pattern='GC_file_Download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
    }

    # -----------------------------------------------------------------------
    # Complete metadata arrays: retain labels containing commas and duplicates
    # -----------------------------------------------------------------------
    ARRAY_COLUMNS = {
        'Participants': ('Study Name', 'Study Accession', 'Samples', 'Primary Diagnosis'),
        'Samples': ('Study Name', 'Study Accession', 'Files', 'Organ or Tissue'),
        'Files': ('Study Name', 'Study Accession', 'Sample ID', 'Participant ID',
                  'Study Data Type', 'Library Strategy', 'Supplementary Files', 'Image Modality'),
    }
    RECORD_IDENTITIES = {'Participants': 'Participant ID', 'Samples': 'Sample ID', 'Files': 'File ID'}

    def prepare_comparison(self, tab, expected, actual, fmt='CSV'):
        if actual.header != expected.header:
            return expected, actual
        identity = expected.header.index(self.RECORD_IDENTITIES[tab])
        expected_rows, actual_rows = [list(row) for row in expected.rows], [list(row) for row in actual.rows]
        ids = [row[identity].strip() for row in expected_rows]
        assert len(ids) == len(set(ids)), f'{tab}: ambiguous expected record identities'
        for name in self.ARRAY_COLUMNS[tab]:
            index = expected.header.index(name)
            labels_by_id = {}
            for row in expected_rows:
                values = json.loads(row[index])
                assert isinstance(values, list) and all(isinstance(value, str) for value in values), \
                    f'{tab} {name}: expected an array of complete metadata labels'
                labels_by_id[row[identity].strip()] = values
                row[index] = json.dumps(sorted(values), ensure_ascii=False)
            for row in actual_rows:
                values = labels_by_id.get(row[identity].strip())
                if values is not None and category_text_matches(row[index], values, separator=','):
                    row[index] = json.dumps(sorted(values), ensure_ascii=False)
                else:
                    row[index] = 'Unexpected values: ' + row[index]

        # GC exports raw bytes; equivalent integer/decimal representations compare equally.
        if tab == 'Files':
            index = expected.header.index('File Size')
            for row in expected_rows + actual_rows:
                value = row[index].strip()
                if value:
                    number = Decimal(value)
                    assert number.is_finite(), 'File Size must contain a finite byte count'
                    value = str(number.normalize())
                row[index] = value
        return Table(expected.header, expected_rows), Table(actual.header, actual_rows)
