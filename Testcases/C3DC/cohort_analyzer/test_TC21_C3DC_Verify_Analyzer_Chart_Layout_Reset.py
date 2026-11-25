"""TC21_C3DC_Verify_Analyzer_Chart_Layout_Reset — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC21_C3DC_Verify_Analyzer_Chart_Layout_Reset(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC21_C3DC_Verify_Analyzer_Chart_Layout_Reset'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.verify_analyzer_layout_reset()
    c3dc.assert_no_failures()
