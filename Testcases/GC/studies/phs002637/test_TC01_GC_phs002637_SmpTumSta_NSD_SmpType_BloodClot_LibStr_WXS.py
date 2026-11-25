"""TC01_GC_phs002637_SmpTumSta-NSD_SmpType-BloodClot_LibStr_WXS — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs002637_SmpTumSta_NSD_SmpType_BloodClot_LibStr_WXS(gc):
    gc.load_query_file('TC01_GC_phs002637_SmpTumSta-NSD_SmpType-BloodClot_LibStr_WXS.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002637')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'NotSpecifiedInData')
    gc.select_filter('SamplesFacet/SampleType', 'BloodClot')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'WXS')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
