"""TC04_GC_phs002366_LibSel-Random_LibLay-PairedEnd_InstMod-IlluminaHiSeqXTen — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs002366_LibSel_Random_LibLay_PairedEnd_InstMod_IlluminaHiSeqXTen(gc):
    gc.load_query_file('TC04_GC_phs002366_LibSel-Random_LibLay-PairedEnd_InstMod-IlluminaHiSeqXTen.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002366')
    gc.select_filter('GenomicFacet/LibrarySelection', 'Random')
    gc.select_filter('GenomicFacet/LibraryLayout', 'Pairedend')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaHiSeqXTen')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
