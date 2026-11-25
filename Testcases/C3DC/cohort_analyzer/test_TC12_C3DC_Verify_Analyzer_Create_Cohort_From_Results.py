"""TC12_C3DC_Verify_Analyzer_Create_Cohort_From_Results — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC12_C3DC_Verify_Analyzer_Create_Cohort_From_Results(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC12_C3DC_Verify_Analyzer_Create_Cohort_From_Results'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC12_C3DC_Verify_Analyzer_Create_Cohort_From_Results', '')
    c3dc.create_analyzer_cohort_from_results()
    c3dc.assert_no_failures()
