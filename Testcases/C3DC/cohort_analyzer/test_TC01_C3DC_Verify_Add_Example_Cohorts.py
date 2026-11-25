"""TC01_C3DC_Verify_Add_Example_Cohorts — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_Verify_Add_Example_Cohorts(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC01_C3DC_Verify_Add_Example_Cohorts'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.verify_example_cohorts_created('Example Cohort 1; Example Cohort 2; Example Cohort 3')
    c3dc.assert_no_failures()
