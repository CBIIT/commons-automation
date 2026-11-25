"""TC17_C3DC_Verify_Analyzer_Build_In_Explore — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC17_C3DC_Verify_Analyzer_Build_In_Explore(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC17_C3DC_Verify_Analyzer_Build_In_Explore'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC17_C3DC_Verify_Analyzer_Build_In_Explore', '')
    c3dc.verify_analyzer_build_explore('You are about to leave this page and continue your analysis of selections in a pre-filtered Explore Dashboard. Press cancel or confirm.')
    c3dc.assert_no_failures()
