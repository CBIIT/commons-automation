"""CTDC result-tab CSV schemas and controls."""
from Commons.result_tabs import DirectCSVResultTabs, ResultTabExportSpec


class CTDCResultTabs(DirectCSVResultTabs):
    # Export columns and independent workbook query names.
    EXPORTS = {
        'Participants': ResultTabExportSpec(
            table_key='ResultTabs/Participants-Tbl',
            download_key='ParticipantsResultTab/CSV',
            format_keys={"CSV": 'ParticipantsResultTab/CSV'},
            headers=('Participant ID', 'Diagnosis', 'Age at Enrollment', 'Sex', 'Race', 'Ethnicity', 'Carcinogen Exposure', 'Therapy', 'Therapy Category', 'Best Response'),
            identity_columns=('Participant ID',),
            query_tab='ParticipantsExportTab', count_query_tab='ParticipantsExportCount',
            filename_pattern='CTDC_Participants_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Biospecimens': ResultTabExportSpec(
            table_key='ResultTabs/Biospecimens-Tbl',
            download_key='BiospecimensResultTab/CSV',
            format_keys={"CSV": 'BiospecimensResultTab/CSV'},
            headers=('Participant ID', 'Diagnosis', 'Primary Site', 'Specimen Record ID', 'Anatomical Collection Site', 'Tissue Category', 'Collection Timepoint'),
            identity_columns=('Specimen Record ID',),
            query_tab='BiospecimensExportTab', count_query_tab='BiospecimensExportCount',
            filename_pattern='CTDC_Biospecimens_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Files': ResultTabExportSpec(
            table_key='ResultTabs/Files-Tbl',
            download_key='FilesResultTab/CSV',
            format_keys={"CSV": 'FilesResultTab/CSV'},
            headers=('Study Accession', 'File Name', 'Format', 'File Type', 'Size', 'Description', 'Access', 'Specimen Record ID', 'Participant ID', 'Diagnosis'),
            identity_columns=('Access',),
            query_tab='FilesExportTab', count_query_tab='FilesExportCount',
            filename_pattern='CTDC_Data_Files_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Study Files': ResultTabExportSpec(
            table_key='ResultTabs/StudyFiles-Tbl',
            download_key='StudyFilesResultTab/CSV',
            format_keys={"CSV": 'StudyFilesResultTab/CSV'},
            headers=('File Name', 'File Type', 'Format', 'Size', 'Description', 'Access', 'Study Accession', 'File UUID'),
            identity_columns=('File UUID',),
            query_tab='StudyFilesExportTab', count_query_tab='StudyFilesExportCount',
            filename_pattern='CTDC_Study_Files_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
    }
    # -----------------------------------------------------------------------
    # Unordered clinical lists retain duplicate values
    # -----------------------------------------------------------------------
    def prepare_comparison(self, tab, expected, actual, fmt='CSV'):
        import json
        from Commons.db_source import Table
        from Commons.result_tabs import category_text_matches
        columns = ('Therapy', 'Therapy Category', 'Best Response') if tab == 'Participants' else ()
        if not columns or actual.header != expected.header:
            return expected, actual
        expected_rows, actual_rows = [list(row) for row in expected.rows], [list(row) for row in actual.rows]
        identity = expected.header.index('Participant ID')
        for name in columns:
            index = expected.header.index(name)
            labels_by_id = {}
            for row in expected_rows:
                values = json.loads(row[index])
                assert isinstance(values, list) and all(isinstance(value, str) for value in values)
                labels_by_id[row[identity]] = values
                row[index] = json.dumps(sorted(values))
            for row in actual_rows:
                values = labels_by_id.get(row[identity])
                if values is not None and category_text_matches(row[index], values):
                    row[index] = json.dumps(sorted(values))
                else:
                    row[index] = 'Unexpected values: ' + row[index]
        return Table(expected.header, expected_rows), Table(actual.header, actual_rows)
