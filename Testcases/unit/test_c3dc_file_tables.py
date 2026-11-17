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


def test_plain_file_cell_does_not_open_a_popup():
    from Commons.apps.c3dc.table_cells import read_file_cell

    ui = Mock()
    ui.text.return_value = 'S1\nS2'
    assert read_file_cell(ui, '//cell') == 'S1; S2'
    ui.loc.assert_not_called()
    ui.click.assert_not_called()


@pytest.mark.parametrize('declared_count', [6, 7])
def test_expanded_file_cell_reads_every_value_and_closes_popup(monkeypatch, declared_count):
    from Commons.apps.c3dc import table_cells

    repo = Mock()
    repo.xpath.side_effect = lambda key: key
    monkeypatch.setattr(table_cells, '_locators', lambda: repo)
    ui = Mock()
    ui.text.side_effect = ['P1\nView All >', str(declared_count)]
    values = [f'P{i}' for i in range(1, 7)]
    ui.loc.return_value.all_text_contents.return_value = values

    if declared_count == len(values):
        assert table_cells.read_file_cell(ui, '//cell') == '; '.join(values)
    else:
        with pytest.raises(AssertionError, match='6 values; expected 7'):
            table_cells.read_file_cell(ui, '//cell')
    ui.click.assert_called_once_with('ResultTabs/FileCellValues-Close')
    assert ui.loc.return_value.wait_for.call_args.kwargs == {'state': 'hidden'}


@pytest.mark.parametrize('displayed,expected_name,accepted', [
    ('run-b', '["run-a","run-b"]', True),
    ('wrong-run', '["run-a","run-b"]', False),
    ('[literal].fastq', '[literal].fastq', False),
])
def test_shared_file_name_requires_database_membership(displayed, expected_name, accepted):
    from Commons.apps.c3dc.table_cells import resolve_file_name_aliases
    from Commons.db_source import Table

    ui = Table(['File Name', 'Participant ID'], [[displayed, 'P1']])
    expected = Table(ui.header[:], [[expected_name, 'P1']])
    assert resolve_file_name_aliases(ui, expected) == int(accepted)
    assert expected.rows[0][0] == (displayed if accepted else expected_name)


def test_shared_filename_resolution_does_not_hide_metadata_mismatches():
    from Commons.apps.c3dc.table_cells import resolve_file_name_aliases
    from Commons.compare import compare_tables
    from Commons.db_source import Table

    ui = Table(['File Name', 'Participant ID'], [['run-b', 'P1']])
    expected = Table(ui.header[:], [['["run-a","run-b"]', 'P2']])
    assert resolve_file_name_aliases(ui, expected) == 1
    assert not compare_tables(ui.rows, expected.rows, ui.header, expected.header).passed


@pytest.mark.parametrize('actual,expected_age,passes', [
    ('2336; Not Reported; 963', '963; 2336; Not Reported', True),
    ('2336; Not Reported; 963', '963; 2337; Not Reported', False),
    ('2336; Not Reported; 963', '2336; Not Reported', False),
    ('963; 963; Not Reported', '963; Not Reported', False),
])
def test_file_age_lists_preserve_all_values_when_order_changes(actual, expected_age, passes):
    from Commons.apps.c3dc import C3DC
    from Commons.compare import compare_tables
    from Commons.db_source import Table

    ui = Table(['Age at Collection'], [[actual]])
    expected = Table(ui.header[:], [[expected_age]])
    app = C3DC.__new__(C3DC)

    app.prepare_tab_comparison(C3DC.TABS['Files'], ui, expected)

    assert compare_tables(ui.rows, expected.rows, ui.header, expected.header).passed == passes


@pytest.mark.parametrize('shown,valid', [
    ('a (10)\nb (5)\nRead More', True),
    ('a (10)\nc (5)\nRead More', True),
    ('a (10)\nc (6)\nRead More', False),
    ('b (5)\nc (5)\nRead More', False),
    ('a (10)\na (10)\nRead More', False),
    ('a (10)\nb (5)', False),
    ('c (5)\na (10)\nRead More', False),
    ('a (10)\nunknown (5)\nRead More', False),
])
def test_ranked_file_types_validate_counts_and_cutoff_ties(shown, valid):
    import json
    from Commons.apps.c3dc.table_cells import resolve_ranked_cells
    from Commons.db_source import Table

    header = ['Study ID', 'File Type (Top 5)']
    source = json.dumps({'ranked_items': ['a (10)', 'b (5)', 'c (5)'], 'top_n': 2})
    ui = Table(header[:], [['study', shown]])
    expected = Table(header[:], [['study', source]])
    assert resolve_ranked_cells(ui, expected) == int(valid)
    assert expected.rows[0][1] == (shown if valid else source)
