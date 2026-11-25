"""TC05_GC_phs002637_Sex-Female_PrimDiag_ProstateCancer_FileType-CRAM — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs002637_Sex_Female_PrimDiag_ProstateCancer_FileType_CRAM(gc):
    gc.load_query_file('TC05_GC_phs002637_Sex-Female_PrimDiag_ProstateCancer_FileType-CRAM.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002637')
    gc.select_filter('DemographicsFacet/Sex', 'Female')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'ProstateCancer')
    gc.select_filter('FilesFacet/FileType', 'cram')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
