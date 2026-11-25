"""PSDC result-tab CSV schemas and controls."""
from Commons.result_tabs import DirectCSVResultTabs, ResultTabExportSpec


class PSDCResultTabs(DirectCSVResultTabs):
    # Export columns and independent workbook query names.
    EXPORTS = {
        'Studies': ResultTabExportSpec(
            table_key='ResultTabs/Studies-Tbl',
            download_key='StudiesResultTab/CSV',
            format_keys={"CSV": 'StudiesResultTab/CSV'},
            headers=('Study Acronym', 'Study Name', 'Enrollment Period', 'Study Period', 'Study Design', 'Study Status', 'Cancer Types', 'Data Categories', 'Biospecimens', 'Enrollment Age', 'Participants'),
            identity_columns=('Study Acronym',),
            query_tab='StudiesExportTab', count_query_tab='StudiesExportCount',
            filename_pattern='PSDC_Studies_download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
    }
