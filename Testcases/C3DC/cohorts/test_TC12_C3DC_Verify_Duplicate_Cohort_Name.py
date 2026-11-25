"""TC12_C3DC_Verify_Duplicate_Cohort_Name — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC12_C3DC_Verify_Duplicate_Cohort_Name(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_participant_page(1)
    c3dc.create_cohort_from_selected_participants()
    c3dc.verify_cohort_created()
    c3dc.update_cohort_details('AutoTest', '')
    c3dc.save_cohort_changes()
    c3dc.verify_cohort_details_saved()
    c3dc.duplicate_selected_cohort()
    c3dc.update_cohort_details('AutoTest', '')
    c3dc.verify_duplicate_cohort_name_rejected('Failed to update cohort: Cohort with Name AutoTest already exists, please choose a different name')
    c3dc.assert_no_failures()
