"""TC05_GC_phs002432_Sex-Female_PrimDiag_MalenomaNOs_FileType-fastq — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs002432_Sex_Female_PrimDiag_MalenomaNOs_FileType_fastq(gc):
    gc.load_query_file('TC05_GC_phs002432_Sex-Female_PrimDiag_MalenomaNOs_FileType-fastq.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002432')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'MelanomaNos')
    gc.select_filter('FilesFacet/FileType', 'fastq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
