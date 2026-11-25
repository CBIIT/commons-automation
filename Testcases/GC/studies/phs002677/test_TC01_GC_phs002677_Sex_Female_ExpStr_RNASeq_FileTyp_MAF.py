"""TC01_GC_phs002677_Sex_Female_ExpStr-RNASeq_FileTyp-MAF — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs002677_Sex_Female_ExpStr_RNASeq_FileTyp_MAF(gc):
    gc.load_query_file('TC01_GC_phs002677_Sex_Female_ExpStr-RNASeq_FileTyp-MAF.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002677')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('FilesFacet/FileType', 'maf')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
