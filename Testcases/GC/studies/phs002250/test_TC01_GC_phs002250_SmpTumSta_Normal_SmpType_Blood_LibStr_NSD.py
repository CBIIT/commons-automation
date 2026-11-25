"""TC01_GC_phs002250_SmpTumSta-Normal_SmpType-Blood_LibStr_NSD — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs002250_SmpTumSta_Normal_SmpType_Blood_LibStr_NSD(gc):
    gc.load_query_file('TC01_GC_phs002250_SmpTumSta-Normal_SmpType-Blood_LibStr_NSD.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002250')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Normal')
    gc.select_filter('SamplesFacet/SampleType', 'Blood')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'NotSpecifiedindata')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
