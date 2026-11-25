"""TC02_C3DC_Verify_Create_NewCohort_SelectedParticipants — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC02_C3DC_Verify_Create_NewCohort_SelectedParticipants(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.verify_selected_participants_option('disabled')
    c3dc.select_participant_page(1)
    c3dc.select_participant_page(2)
    c3dc.verify_selected_participants_option('enabled')
    c3dc.create_cohort_from_selected_participants()
    c3dc.verify_cohort_created()
    c3dc.assert_no_failures()
