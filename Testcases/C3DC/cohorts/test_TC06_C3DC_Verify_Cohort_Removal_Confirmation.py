"""TC06_C3DC_Verify_Cohort_Removal_Confirmation — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC06_C3DC_Verify_Cohort_Removal_Confirmation(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.select_filter('Demographics/Race', 'American Indian or Alaska Native')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.duplicate_cohort_repeatedly(3)
    c3dc.verify_cohort_removal_confirmation('table', 'Are you sure you want to delete this cohort? This will permanently delete the cohort and all associated participants. Please confirm or cancel.')
    c3dc.verify_cohort_removal_confirmation('cohort', 'Are you sure you want to delete this cohort? This will permanently delete the cohort and all associated participants. Please confirm or cancel.')
    c3dc.verify_cohort_removal_confirmation('all', 'Are you sure you want to delete all cohorts? This action cannot be undone. Press Confirm or Cancel.')
    c3dc.assert_no_failures()
