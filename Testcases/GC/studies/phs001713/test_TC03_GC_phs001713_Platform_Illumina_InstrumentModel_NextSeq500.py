"""TC03_GC_phs001713_Platform-Illumina_InstrumentModel-NextSeq500 — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs001713_Platform_Illumina_InstrumentModel_NextSeq500(gc):
    gc.load_query_file('TC03_GC_phs001713_Platform-Illumina_InstrumentModel-NextSeq500.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001713')
    gc.select_filter('SequencingFacet/Platform', 'ILLUMINA')
    gc.select_filter('SequencingFacet/InstrumentModel', 'IlluminaNextSeq500')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
