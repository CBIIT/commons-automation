"""TC02_GC_phs001524_SampleTumorStatus-NSD_SampleType-Blood — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC02_GC_phs001524_SampleTumorStatus_NSD_SampleType_Blood(gc):
    gc.load_query_file('TC02_GC_phs001524_SampleTumorStatus-NSD_SampleType-Blood.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001524')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'NotSpecifiedInData')
    gc.select_filter('SamplesFacet/SampleType', 'Blood')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
