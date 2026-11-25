"""TC01_GC_phs001905_SmpTumSta-NSD_SmpType-Tissue_LibStr_TargetedCapture — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs001905_SmpTumSta_NSD_SmpType_Tissue_LibStr_TargetedCapture(gc):
    gc.load_query_file('TC01_GC_phs001905_SmpTumSta-NSD_SmpType-Tissue_LibStr_TargetedCapture.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001905')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'NotSpecifiedInData')
    gc.select_filter('SamplesFacet/SampleType', 'Tissue')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'TargetedCapture')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
