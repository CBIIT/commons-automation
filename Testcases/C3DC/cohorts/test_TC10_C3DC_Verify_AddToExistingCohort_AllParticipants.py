"""TC10_C3DC_Verify_AddToExistingCohort_AllParticipants — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC10_C3DC_Verify_AddToExistingCohort_AllParticipants(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.remember_cohort_for_addition()
    c3dc.close_cohorts()
    c3dc.replace_cohort_filter('Diagnosis/Diagnosis', 'AbdominalFibromatosis', 'Adenocarcinoma')
    c3dc.add_all_participants_to_existing_cohort()
    c3dc.verify_participants_added_to_cohort('TC10_C3DC_Verify_AddToExistingCohort_AllParticipants')
    c3dc.assert_no_failures()
