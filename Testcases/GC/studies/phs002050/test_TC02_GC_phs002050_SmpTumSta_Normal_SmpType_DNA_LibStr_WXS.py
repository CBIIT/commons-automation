"""TC02_GC_phs002050_SmpTumSta-Normal_SmpType-DNA_LibStr_WXS — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs002050_SmpTumSta_Normal_SmpType_DNA_LibStr_WXS(gc):
    gc.load_query_file('TC02_GC_phs002050_SmpTumSta-Normal_SmpType-DNA_LibStr_WXS.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002050')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Normal')
    gc.select_filter('SamplesFacet/SampleType', 'DNA')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'WXS')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
