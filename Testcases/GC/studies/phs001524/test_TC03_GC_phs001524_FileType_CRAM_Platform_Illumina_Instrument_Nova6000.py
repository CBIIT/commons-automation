"""TC03_GC_phs001524_FileType-CRAM_Platform-Illumina_Instrument-Nova6000 — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs001524_FileType_CRAM_Platform_Illumina_Instrument_Nova6000(gc):
    gc.load_query_file('TC03_GC_phs001524_FileType-CRAM_Platform-Illumina_Instrument-Nova6000.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001524')
    gc.select_filter('FilesFacet/FileType', 'cram')
    gc.select_filter('GenomicFacet/Platform', 'ILLUMINA')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaNovaSeq6000')
    gc.read_statbar()
    gc.verify_tab('Samples')
    gc.assert_no_failures()
