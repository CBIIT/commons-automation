"""TC09_C3DC_Verify_Cohort_Control_Tooltips — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC09_C3DC_Verify_Cohort_Control_Tooltips(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.select_filter('Demographics/Race', 'American Indian or Alaska Native')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.close_cohorts()
    c3dc.verify_cohort_tooltip('CreateNewHelp', 'Create a new cohort using the selected Participant IDs. Note: The optimal number of participants in a cohort is =< 4000 participants')
    c3dc.verify_cohort_tooltip('AddExistingHelp', 'Add selected Participant IDs to an existing cohort. Note: The optimal number of participants in a cohort is =< 4000 participants')
    c3dc.verify_cohort_tooltip('ViewAllHelp', 'Click to view the complete list of all cohorts')
    c3dc.open_cohorts()
    c3dc.verify_cohort_tooltip('DeleteAll', 'Remove all Cohorts')
    c3dc.verify_cohort_tooltip('DeleteSelected', 'Remove Cohort')
    c3dc.verify_cohort_tooltip('DuplicateSelected', 'Duplicate Cohort')
    c3dc.assert_no_failures()
