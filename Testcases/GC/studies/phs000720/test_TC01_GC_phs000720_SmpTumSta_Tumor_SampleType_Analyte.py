"""TC01_GC_phs000720_SmpTumSta-Tumor_SampleType_Analyte — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs000720_SmpTumSta_Tumor_SampleType_Analyte(gc):
    gc.load_query_file('TC01_GC_phs000720_SmpTumSta-Tumor_SampleType_Analyte.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs000720')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Tumor')
    gc.select_filter('SamplesFacet/SampleType', 'Analyte')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
