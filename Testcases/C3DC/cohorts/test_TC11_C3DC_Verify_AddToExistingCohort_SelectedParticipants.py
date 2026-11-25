"""TC11_C3DC_Verify_AddToExistingCohort_SelectedParticipants — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC11_C3DC_Verify_AddToExistingCohort_SelectedParticipants(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_participant_page(1)
    c3dc.create_cohort_from_selected_participants()
    c3dc.verify_cohort_created()
    c3dc.remember_cohort_for_addition()
    c3dc.close_cohorts()
    c3dc.select_next_participant_page_only()
    c3dc.add_selected_participants_to_existing_cohort()
    c3dc.verify_participants_added_to_cohort('TC11_C3DC_Verify_AddToExistingCohort_SelectedParticipants')
    c3dc.assert_no_failures()
