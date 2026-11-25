"""TC06_C3DC_Verify_Analyzer_Cohort_Sorting — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC06_C3DC_Verify_Analyzer_Cohort_Sorting(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC06_C3DC_Verify_Analyzer_Cohort_Sorting'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC06_C3DC_Verify_Analyzer_Cohort_Sorting', '')
    c3dc.verify_analyzer_sorting()
    c3dc.assert_no_failures()
