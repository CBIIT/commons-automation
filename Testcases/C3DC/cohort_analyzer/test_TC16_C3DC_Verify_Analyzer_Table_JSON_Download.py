"""TC16_C3DC_Verify_Analyzer_Table_JSON_Download — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC16_C3DC_Verify_Analyzer_Table_JSON_Download(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC16_C3DC_Verify_Analyzer_Table_JSON_Download'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC16_C3DC_Verify_Analyzer_Table_JSON_Download', 'clinical')
    c3dc.verify_analyzer_table_download('JSON')
    c3dc.assert_no_failures()
