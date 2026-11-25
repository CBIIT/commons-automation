"""TC03_GC_phs001819_Platform-Illumina_InstrumentModel-HiSeq2000 — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs001819_Platform_Illumina_InstrumentModel_HiSeq2000(gc):
    gc.load_query_file('TC03_GC_phs001819_Platform-Illumina_InstrumentModel-HiSeq2000.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001819')
    gc.select_filter('GenomicFacet/Platform', 'ILLUMINA')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaHiSeq2000')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
