"""TC02_GC_phs003155_SampleTumorStatus-Tumor_SampleType-Metastatic — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs003155_SampleTumorStatus_Tumor_SampleType_Metastatic(gc):
    gc.load_query_file('TC02_GC_phs003155_SampleTumorStatus-Tumor_SampleType-Metastatic.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs003155')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Tumor')
    gc.select_filter('SamplesFacet/SampleType', 'Metastatic')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
