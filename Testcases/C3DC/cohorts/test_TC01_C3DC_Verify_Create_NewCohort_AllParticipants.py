"""TC01_C3DC_Verify_Create_NewCohort_AllParticipants — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_Verify_Create_NewCohort_AllParticipants(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.select_filter('Demographics/Race', 'American Indian or Alaska Native')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.assert_no_failures()
