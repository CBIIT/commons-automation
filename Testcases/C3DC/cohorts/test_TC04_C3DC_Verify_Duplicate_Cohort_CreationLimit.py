"""TC04_C3DC_Verify_Duplicate_Cohort_CreationLimit — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC04_C3DC_Verify_Duplicate_Cohort_CreationLimit(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.select_filter('Demographics/Race', 'American Indian or Alaska Native')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.close_cohorts()
    c3dc.open_cohorts()
    c3dc.duplicate_cohort_repeatedly(19)
    c3dc.verify_duplicate_cohort_limit()
    c3dc.assert_no_failures()
