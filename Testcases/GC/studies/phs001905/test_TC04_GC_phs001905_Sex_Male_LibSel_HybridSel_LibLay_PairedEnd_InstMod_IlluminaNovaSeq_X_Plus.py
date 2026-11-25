"""TC04_GC_phs001905_Sex_Male_LibSel-HybridSel_LibLay-PairedEnd_InstMod-IlluminaNovaSeq X Plus — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs001905_Sex_Male_LibSel_HybridSel_LibLay_PairedEnd_InstMod_IlluminaNovaSeq_X_Plus(gc):
    gc.load_query_file('TC04_GC_phs001905_Sex_Male_LibSel-HybridSel_LibLay-PairedEnd_InstMod-IlluminaNovaSeq X Plus.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001905')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('GenomicFacet/LibrarySelection', 'HybridSelection')
    gc.select_filter('GenomicFacet/LibraryLayout', 'Pairedend')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaNovaSeqXPlus')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
