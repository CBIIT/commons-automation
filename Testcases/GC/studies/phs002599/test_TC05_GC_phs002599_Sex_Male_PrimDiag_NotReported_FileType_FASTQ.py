"""TC05_GC_phs002599_Sex-Male_PrimDiag_NotReported_FileType-FASTQ — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs002599_Sex_Male_PrimDiag_NotReported_FileType_FASTQ(gc):
    gc.load_query_file('TC05_GC_phs002599_Sex-Male_PrimDiag_NotReported_FileType-FASTQ.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002599')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'NotReported')
    gc.select_filter('FilesFacet/FileType', 'fastq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
