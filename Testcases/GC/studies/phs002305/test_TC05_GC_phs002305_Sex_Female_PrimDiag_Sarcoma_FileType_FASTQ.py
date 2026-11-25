"""TC05_GC_phs002305_Sex-Female_PrimDiag_Sarcoma_FileType-FASTQ — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs002305_Sex_Female_PrimDiag_Sarcoma_FileType_FASTQ(gc):
    gc.load_query_file('TC05_GC_phs002305_Sex-Female_PrimDiag_Sarcoma_FileType-FASTQ.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002305')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'SarcomaNOS')
    gc.select_filter('FilesFacet/FileType', 'fastq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
