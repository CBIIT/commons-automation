"""TC02_GC_phs002293_Sex_Female_ExpStr-WXS_FileTyp-VCF — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs002293_Sex_Female_ExpStr_WXS_FileTyp_VCF(gc):
    gc.load_query_file('TC02_GC_phs002293_Sex_Female_ExpStr-WXS_FileTyp-VCF.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002293')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'WXS')
    gc.select_filter('FilesFacet/FileType', 'vcf')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
