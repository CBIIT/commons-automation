"""TC08_C3DC_Verify_Cohort_MetadataJson_Download — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC08_C3DC_Verify_Cohort_MetadataJson_Download(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs002790')
    c3dc.select_filter('Demographics/Race', 'American Indian or Alaska Native')
    c3dc.create_cohort_from_all_participants()
    c3dc.verify_cohort_created()
    c3dc.download_cohort_metadata('TC08_C3DC_Verify_Cohort_MetadataJson_Download')
    c3dc.verify_cohort_metadata()
    c3dc.assert_no_failures()
