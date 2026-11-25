"""TC01_GC_phs001819_Sex-Female_ExperimentalStrategy-WXS — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs001819_Sex_Female_ExperimentalStrategy_WXS(gc):
    gc.load_query_file('TC01_GC_phs001819_Sex-Female_ExperimentalStrategy-WXS.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001819')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'WXS')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
