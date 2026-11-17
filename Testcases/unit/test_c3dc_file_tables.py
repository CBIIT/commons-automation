"""Explore Files keeps all metadata columns aligned and preserves complete lists."""
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc import C3DC
from Commons.table_reader import read_table_header_data, read_table_row_data

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("table,headers,cells,keep", [
    ("file_tab_table", ["Select all", "File Name", "Participant ID", "Sample ID", "Tumor Spatial Extent"],
     ["", "a.dcm", "P1", "S2\nS1", "Local"], [1, 2, 3, 4]),
    ("imaging_data_tab_table", ["Study UID", "Series UID", "Sample ID", "IDC Histopathology Viewer", "Magnification"],
     ["2.25.123", "1.2.3", "S2\nS1", "View Pathology Study/Series", "40X"], [0, 1, 2, 4]),
])
def test_file_tables_keep_headers_and_cells_aligned(table, headers, cells, keep):
    main = f"//*[@id='{table}']"
    body = main + "//tbody"
    ui = Mock()
    ui.text.side_effect = lambda xp: cells[int(xp.rsplit("[", 1)[1][:-1]) - 1]

    assert read_table_header_data("C3DC", main, headers) == [headers[i] for i in keep]
    assert read_table_row_data("C3DC", ui, tbl_main=main, tbl_bdy=body,
                               row_index=1, col_header=headers, trace=False) == [
        cells[i].replace("\n", "; ") for i in keep
    ]
    assert len(ui.text.call_args_list) == len(keep)


def test_explore_files_navigation_retains_current_study_filter():
    app = C3DC.__new__(C3DC)
    app._active_study_accession = "phs002790"
    app.click = Mock()
    app._wait_explore_results_ready = Mock()

    app.open_explore_files()

    app.click.assert_called_once_with("Navbar/Explore-Files-Tab", ui_message="Explore Files opened successfully.")
    app._wait_explore_results_ready.assert_called_once_with()
    assert app._active_study_accession == "phs002790"
    assert C3DC.STANDARD_VERIFY_TABS == ("Participants", "Studies", "Genetic Analysis", "Samples")
