"""TC03_GC_phs001554_FileType-CRAI_Platform-Illumina_Instrument-HiSeq2500 — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs001554_FileType_CRAI_Platform_Illumina_Instrument_HiSeq2500(gc):
    gc.load_query_file('TC03_GC_phs001554_FileType-CRAI_Platform-Illumina_Instrument-HiSeq2500.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001554')
    gc.select_filter('FilesFacet/FileType', 'crai')
    gc.select_filter('GenomicFacet/Platform', 'ILLUMINA')
    gc.select_filter('GenomicFacet/InstrumentModel', 'IlluminaHiSeq2500')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
