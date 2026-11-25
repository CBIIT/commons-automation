"""TC05_GC_phs003432_Sex-Female_PrimDiag_NotReported_FileType-RDS — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs003432_Sex_Female_PrimDiag_NotReported_FileType_RDS(gc):
    gc.load_query_file('TC05_GC_phs003432_Sex-Female_PrimDiag_NotReported_FileType-RDS.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs003432')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'NotReported')
    gc.select_filter('FilesFacet/FileType', 'rds')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
