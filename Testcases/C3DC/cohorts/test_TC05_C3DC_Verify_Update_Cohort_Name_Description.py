"""TC05_C3DC_Verify_Update_Cohort_Name_Description — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC05_C3DC_Verify_Update_Cohort_Name_Description(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.select_filter('Demographics/Race', 'American Indian or Alaska Native')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.update_cohort_details('Updated AIAN Cohort', 'Participants from study phs002790 with race American Indian or Alaska Native. Updated cohort description.')
    c3dc.save_cohort_changes()
    c3dc.verify_cohort_details_saved()
    c3dc.assert_no_failures()
