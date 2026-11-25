"""TC06_GC_phs000720_PrimDiag_NotApplicable — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC06_GC_phs000720_PrimDiag_NotApplicable(gc):
    gc.load_query_file('TC06_GC_phs000720_PrimDiag_NotApplicable.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs000720')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'NotApplicable')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
