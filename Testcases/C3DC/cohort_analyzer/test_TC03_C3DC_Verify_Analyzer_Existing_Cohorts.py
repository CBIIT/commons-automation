"""TC03_C3DC_Verify_Analyzer_Existing_Cohorts — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC03_C3DC_Verify_Analyzer_Existing_Cohorts(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_participant_page(1)
    c3dc.create_cohort_from_selected_participants()
    c3dc.verify_cohort_created()
    c3dc.close_cohorts()
    c3dc._analyzer_output = c3dc.output_dir / 'TC03_C3DC_Verify_Analyzer_Existing_Cohorts'
    c3dc.open_cohort_analyzer()
    c3dc.remember_analyzer_cohorts('TC03_C3DC_Verify_Analyzer_Existing_Cohorts', '')
    c3dc.verify_analyzer_existing_cohorts()
    c3dc.assert_no_failures()
