"""TC13_C3DC_Verify_Cohort_Participant_Search_Removal — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC13_C3DC_Verify_Cohort_Participant_Search_Removal(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_participant_page(1)
    c3dc.create_cohort_from_selected_participants()
    c3dc.verify_cohort_created()
    c3dc.verify_cohort_participant_search()
    c3dc.remove_cohort_participant()
    c3dc.verify_cohort_participant_removed()
    c3dc.assert_no_failures()
