"""TC01_GC_phs002430_Sex-Unknown_SmpTumSta-Tumor_SmpType-NotSpecifiedindata_Filetype-fastq — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.quickrun
@pytest.mark.regression
def test_TC01_GC_phs002430_Sex_Unknown_SmpTumSta_Tumor_SmpType_NotSpecifiedindata_Filetype_fastq(gc):
    gc.load_query_file('TC01_GC_phs002430_Sex-Unknown_SmpTumSta-Tumor_SmpType-NotSpecifiedindata_Filetype-fastq.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002430')
    gc.select_filter('DemographicsFacet/Sex', 'Unknown')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Tumor')
    gc.select_filter('SamplesFacet/SampleType', 'NotSpecifiedInData')
    gc.select_filter('FilesFacet/FileType', 'fastq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
