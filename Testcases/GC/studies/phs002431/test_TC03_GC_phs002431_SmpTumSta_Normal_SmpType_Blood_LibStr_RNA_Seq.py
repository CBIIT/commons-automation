"""TC03_GC_phs002431_SmpTumSta-Normal_SmpType-Blood_LibStr_RNA-Seq — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs002431_SmpTumSta_Normal_SmpType_Blood_LibStr_RNA_Seq(gc):
    gc.load_query_file('TC03_GC_phs002431_SmpTumSta-Normal_SmpType-Blood_LibStr_RNA-Seq.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002431')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Normal')
    gc.select_filter('SamplesFacet/SampleType', 'Blood')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'WGS')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
