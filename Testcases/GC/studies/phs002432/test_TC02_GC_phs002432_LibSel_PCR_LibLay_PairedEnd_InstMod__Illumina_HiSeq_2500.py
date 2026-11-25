"""TC02_GC_phs002432_LibSel-PCR_LibLay-PairedEnd_InstMod- Illumina HiSeq 2500 — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs002432_LibSel_PCR_LibLay_PairedEnd_InstMod__Illumina_HiSeq_2500(gc):
    gc.load_query_file('TC02_GC_phs002432_LibSel-PCR_LibLay-PairedEnd_InstMod- Illumina HiSeq 2500.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002432')
    gc.select_filter('GenomicFacet/LibrarySelection', 'PCR')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaHiSeq2500')
    gc.select_filter('GenomicFacet/LibraryLayout', 'Pairedend')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
