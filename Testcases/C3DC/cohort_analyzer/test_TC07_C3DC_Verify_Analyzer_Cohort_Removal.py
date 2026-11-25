"""TC07_C3DC_Verify_Analyzer_Cohort_Removal — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC07_C3DC_Verify_Analyzer_Cohort_Removal(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC07_C3DC_Verify_Analyzer_Cohort_Removal'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC07_C3DC_Verify_Analyzer_Cohort_Removal', '')
    c3dc.verify_analyzer_removal('cohort', 'Are you sure you want to delete this cohort? This action cannot be undone. Press Confirm or Cancel.')
    c3dc.verify_analyzer_removal('all', 'Are you sure you want to delete ALL cohorts? This action cannot be undone. Press Confirm or Cancel.')
    c3dc.assert_no_failures()
