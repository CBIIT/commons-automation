"""TC15_C3DC_Verify_Analyzer_Table_CSV_Download — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC15_C3DC_Verify_Analyzer_Table_CSV_Download(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC15_C3DC_Verify_Analyzer_Table_CSV_Download'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC15_C3DC_Verify_Analyzer_Table_CSV_Download', '')
    c3dc.verify_analyzer_table_download('CSV')
    c3dc.assert_no_failures()
