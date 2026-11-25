"""TC01_GC_phs001437_Sex-Unknown_ExperimentalStrategy-RNASeq — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs001437_Sex_Unknown_ExperimentalStrategy_RNASeq(gc):
    gc.load_query_file('TC01_GC_phs001437_Sex-Unknown_ExperimentalStrategy-RNASeq.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001437')
    gc.select_filter('DemographicsFacet/Sex', 'Unknown')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'RNASeq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
