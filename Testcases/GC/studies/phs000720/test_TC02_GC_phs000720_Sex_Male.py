"""TC02_GC_phs000720_Sex_Male — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.quickrun
@pytest.mark.regression
@pytest.mark.smoke
def test_TC02_GC_phs000720_Sex_Male(gc):
    gc.load_query_file('TC02_GC_phs000720_Sex_Male.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs000720')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
