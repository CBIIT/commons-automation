"""ICDC result-tab CSV schemas and controls."""
from Commons.result_tabs import DirectCSVResultTabs, ResultTabExportSpec


class ICDCResultTabs(DirectCSVResultTabs):
    # Export columns and independent workbook query names.
    EXPORTS = {
        'Cases': ResultTabExportSpec(
            table_key='Canine_CasesTable',
            download_key='CasesResultTab/CSV',
            format_keys={"CSV": 'CasesResultTab/CSV'},
            headers=('Case ID', 'Study Code', 'Study Type', 'Breed', 'Diagnosis', 'Stage Of Disease', 'Age', 'Sex', 'Neutered Status', 'Weight (kg)', 'Response to Treatment', 'Cohort', 'Canine ID', 'Matching Cases', 'Disease Site', 'Date of Diagnosis', 'Histology/Cytopathology', 'Histological Grade', 'Detailed Pathology Evaluation Available', 'Treatment Data Available', 'Follow Up Data Available', 'Concurrent Disease(s)', 'Concurrent Disease Specifics', 'Arm'),
            identity_columns=('Case ID',),
            query_tab='CasesExportTab', count_query_tab='CasesExportCount',
            filename_pattern='ICDC_Cases_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Samples': ResultTabExportSpec(
            table_key='Canine_Samples_Table',
            download_key='SamplesResultTab/CSV',
            format_keys={"CSV": 'SamplesResultTab/CSV'},
            headers=('Sample ID', 'Case ID', 'Breed', 'Diagnosis', 'Sample Site', 'Sample Type', 'Pathology/Morphology', 'Tumor Grade', 'Sample Chronology', 'Percentage Tumor', 'Necropsy Sample', 'Sample Preservation', 'Physical Sample Type', 'General Sample Pathology', 'Tumor Sample Origin', 'Sample Comments', 'Canine ID', 'Matching Cases', 'Age', 'Sex', 'Neutered Status', 'Weight (kg)', 'Disease Site', 'Stage of Disease', 'Date of Diagnosis', 'Histology/Cytopathology', 'Histological Grade', 'Response to Treatment', 'Detailed Pathology Evaluation Available', 'Treatment Data Available', 'Follow Up Data Available', 'Concurrent Disease(s)', 'Concurrent Disease Specifics', 'Cohort', 'Arm'),
            identity_columns=('Sample ID',),
            query_tab='SamplesExportTab', count_query_tab='SamplesExportCount',
            filename_pattern='ICDC_Samples_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Case Files': ResultTabExportSpec(
            table_key='Canine_Files_Table',
            download_key='CaseFilesResultTab/CSV',
            format_keys={"CSV": 'CaseFilesResultTab/CSV'},
            headers=('File Name', 'File Type', 'Association', 'Description', 'Format', 'Size', 'Sample ID', 'Case ID', 'File UUID', 'Breed', 'Diagnosis', 'Study Code', 'Sample Site', 'Physical Sample Type', 'General Sample Pathology', 'Tumor Sample Origin', 'Sample Type', 'Pathology/Morphology', 'Sample Collection Date', 'Tumor Grade', 'Sample Chronology', 'Percentage Tumor', 'Necropsy Sample', 'Sample Preservation', 'Sample Comments', 'Canine ID', 'Age', 'Sex', 'Neutered Status', 'Weight (kg)', 'Disease Site', 'Stage of Disease', 'Date of Diagnosis', 'Histology/Cytopathology', 'Histological Grade', 'Response to Treatment', 'Detailed Pathology Evaluation Available', 'Treatment Data Available', 'Follow Up Data Available', 'Concurrent Disease(s)', 'Concurrent Disease Specifics', 'Cohort', 'Arm', 'Matching Cases'),
            identity_columns=('File UUID',),
            query_tab='CaseFilesExportTab', count_query_tab='CaseFilesExportCount',
            filename_pattern='ICDC_Files_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Study Files': ResultTabExportSpec(
            table_key='Canine_StudyFiles_Table',
            download_key='StudyFilesResultTab/CSV',
            format_keys={"CSV": 'StudyFilesResultTab/CSV'},
            headers=('File Name', 'File Type', 'Association', 'Description', 'Format', 'Size', 'Study Code'),
            identity_columns=('File Name',),
            query_tab='StudyFilesExportTab', count_query_tab='StudyFilesExportCount',
            filename_pattern='ICDC_Study_Files_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
    }
    # -----------------------------------------------------------------------
    # File sizes: the CSV uses the portal's rounded display units
    # -----------------------------------------------------------------------
    def prepare_comparison(self, tab, expected, actual, fmt='CSV'):
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
        from Commons.db_source import Table
        def numeric_values(table):
            rows = [list(row) for row in table.rows]
            for row in rows:
                for name in ('Age', 'Weight (kg)', 'Percentage Tumor'):
                    if name in table.header:
                        index = table.header.index(name)
                        try:
                            row[index] = str(Decimal(row[index]).normalize())
                        except InvalidOperation:
                            pass  # Missing-value labels remain literal and must still match.
            return Table(table.header, rows)
        expected, actual = numeric_values(expected), numeric_values(actual)
        if 'Size' not in expected.header:
            return expected, actual
        index = expected.header.index('Size')
        rows = [list(row) for row in expected.rows]
        for row in rows:
            if not row[index]:
                continue
            size = Decimal(row[index])
            units = ('B', 'KB', 'MB', 'GB', 'TB')
            unit = 0
            while size >= 1024 and unit < len(units) - 1:
                size /= 1024
                unit += 1
            row[index] = f'{size.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):f}'.rstrip('0').rstrip('.') + ' ' + units[unit]
        return Table(expected.header, rows), actual
