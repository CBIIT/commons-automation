"""INS result-tab CSV schemas and controls."""
from Commons.result_tabs import DirectCSVResultTabs, ResultTabExportSpec


class INSResultTabs(DirectCSVResultTabs):
    # Export columns and independent workbook query names.
    EXPORTS = {
        'Programs': ResultTabExportSpec(
            table_key='ResultTabs/Programs-Tbl',
            download_key='ProgramsResultTab/CSV',
            format_keys={"CSV": 'ProgramsResultTab/CSV'},
            headers=('Program', 'Website', 'Special Topic', 'Cancer Type', 'Data Location Details'),
            identity_columns=('Program',),
            query_tab='ProgramsExportTab', count_query_tab='ProgramsExportCount',
            filename_pattern='INS\\ programs\\ download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Projects': ResultTabExportSpec(
            table_key='ResultTabs/Projects-Tbl',
            download_key='ProjectsResultTab/CSV',
            format_keys={"CSV": 'ProjectsResultTab/CSV'},
            headers=('Project ID', 'Project Title', 'Program(s)', 'Organization', 'Project Start Date', 'Project End Date'),
            identity_columns=('Project ID',),
            query_tab='ProjectsExportTab', count_query_tab='ProjectsExportCount',
            filename_pattern='INS\\ projects\\ download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Grants': ResultTabExportSpec(
            table_key='ResultTabs/Grants-Tbl',
            download_key='GrantsResultTab/CSV',
            format_keys={"CSV": 'GrantsResultTab/CSV'},
            headers=('Grant ID', 'Project', 'Grant Title', 'Principal Investigators', 'Program Officers', 'Fiscal Year', 'Project End Date'),
            identity_columns=('Grant ID',),
            query_tab='GrantsExportTab', count_query_tab='GrantsExportCount',
            filename_pattern='INS\\ grants\\ download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
        'Publications': ResultTabExportSpec(
            table_key='ResultTabs/Publications-Tbl',
            download_key='PublicationsResultTab/CSV',
            format_keys={"CSV": 'PublicationsResultTab/CSV'},
            headers=('PubMed ID', 'Project(s)', 'Title', 'Authors', 'Publication Date', 'Cited By', 'Relative Citation Ratio'),
            identity_columns=('PubMed ID',),
            query_tab='PublicationsExportTab', count_query_tab='PublicationsExportCount',
            filename_pattern='INS\\ publications\\ download \\d{4}-\\d{2}-\\d{2} \\d{2}-\\d{2}-\\d{2}\\.csv',
        ),
    }
    # -----------------------------------------------------------------------
    # Numeric export values and unordered metadata lists
    # -----------------------------------------------------------------------
    def prepare_comparison(self, tab, expected, actual, fmt='CSV'):
        from decimal import Decimal
        from Commons.db_source import Table
        arrays = {'Programs': ('Cancer Type',), 'Projects': ('Program(s)',),
                  'Grants': ('Principal Investigators', 'Program Officers'),
                  'Publications': ('Project(s)', 'Authors')}[tab]
        def normalize(table):
            rows = [list(row) for row in table.rows]
            for row in rows:
                for name in arrays:
                    i = table.header.index(name)
                    row[i] = ';'.join(sorted(value.strip() for value in row[i].split(';') if value.strip()))
                for name in ('Cited By', 'Relative Citation Ratio', 'Fiscal Year'):
                    if name in table.header:
                        i = table.header.index(name)
                        row[i] = row[i].strip()
                        if row[i]:
                            row[i] = str(Decimal(row[i]).normalize())
            return Table(table.header, rows)
        return normalize(expected), normalize(actual)
