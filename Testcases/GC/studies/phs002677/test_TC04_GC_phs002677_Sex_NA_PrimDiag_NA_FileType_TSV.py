"""TC04_GC_phs002677_Sex-NA_PrimDiag_NA_FileType-TSV — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs002677_Sex_NA_PrimDiag_NA_FileType_TSV(gc):
    gc.load_query_file('TC04_GC_phs002677_Sex-NA_PrimDiag_NA_FileType-TSV.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002677')
    gc.select_filter('DemographicsFacet/Sex', 'NotApplicable')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'NotApplicable')
    gc.select_filter('FilesFacet/FileType', 'tsv')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
