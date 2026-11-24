"""C3DC pagination contracts; all interaction and verification live in Commons."""
from Commons.table_pagination import PaginationOptions
from Commons.table_reader import active_result_tab_record_count


# ---------------------------------------------------------------------------
# Visible record identities and the independent total in the selected result tab
# ---------------------------------------------------------------------------

IDENTITY_COLUMNS = {
    'Studies': ('Study ID',), 'Participants': ('Participant ID',),
    'Samples': ('Sample ID',), 'GeneticAnalysis': ('Genetic Analysis ID',),
    'Files': ('File Name',), 'ImagingData': ('Study UID', 'Series UID'),
}


def pagination_options(app, tab):
    return PaginationOptions(identity_columns=IDENTITY_COLUMNS[tab],
                             link_columns=('IDC Histopathology Viewer',) if tab == 'ImagingData' else (),
                             total_reader=lambda: active_result_tab_record_count(app.ui),
                             size_change_policy='first')
