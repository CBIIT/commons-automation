"""TC02_GC_phs001905_Sex_Unknown_ExpStr-TargetedSeq_FileTyp-CRAM — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs001905_Sex_Unknown_ExpStr_TargetedSeq_FileTyp_CRAM(gc):
    gc.load_query_file('TC02_GC_phs001905_Sex_Unknown_ExpStr-TargetedSeq_FileTyp-CRAM.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001905')
    gc.select_filter('DemographicsFacet/Sex', 'Unknown')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'TargetedSequencing')
    gc.select_filter('FilesFacet/FileType', 'cram')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
