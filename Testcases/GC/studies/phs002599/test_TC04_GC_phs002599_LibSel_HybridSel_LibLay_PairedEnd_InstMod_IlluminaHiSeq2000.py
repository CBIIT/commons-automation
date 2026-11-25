"""TC04_GC_phs002599_LibSel-HybridSel_LibLay-PairedEnd_InstMod-IlluminaHiSeq2000 — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs002599_LibSel_HybridSel_LibLay_PairedEnd_InstMod_IlluminaHiSeq2000(gc):
    gc.load_query_file('TC04_GC_phs002599_LibSel-HybridSel_LibLay-PairedEnd_InstMod-IlluminaHiSeq2000.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002599')
    gc.select_filter('GenomicFacet/LibrarySelection', 'HybridSelection')
    gc.select_filter('GenomicFacet/LibraryLayout', 'Pairedend')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaHiSeq2000')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
