"""TC04_GC_phs001787_SamTumSt-Normal_LibrStrtg-WXS_LibrSourMol-GenomicDNA — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs001787_SamTumSt_Normal_LibrStrtg_WXS_LibrSourMol_GenomicDNA(gc):
    gc.load_query_file('TC04_GC_phs001787_SamTumSt-Normal_LibrStrtg-WXS_LibrSourMol-GenomicDNA.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001787')
    gc.select_filter('SamplesFacet/SampleTumorStatus', 'Normal')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'WXS')
    gc.select_filter('GenomicFacet/LibrarySource', 'Genomic')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
