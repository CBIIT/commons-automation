"""TC13_C3DC_Verify_Analyzer_Participant_Table — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC13_C3DC_Verify_Analyzer_Participant_Table(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC13_C3DC_Verify_Analyzer_Participant_Table'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC13_C3DC_Verify_Analyzer_Participant_Table', 'clinical')
    c3dc.verify_analyzer_table()
    c3dc.assert_no_failures()
