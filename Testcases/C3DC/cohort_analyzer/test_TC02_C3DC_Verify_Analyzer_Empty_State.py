"""TC02_C3DC_Verify_Analyzer_Empty_State — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC02_C3DC_Verify_Analyzer_Empty_State(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC02_C3DC_Verify_Analyzer_Empty_State'
    c3dc.open_cohort_analyzer()
    c3dc.verify_analyzer_empty_state()
    c3dc.assert_no_failures()
