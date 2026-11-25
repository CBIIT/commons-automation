"""TC03_GC_Verify_Participants_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_Verify_Participants_Tab_Sorting(gc):
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs000720')
    gc.select_filter('FilesFacet/FileType', 'hdf5')
    gc.verify_result_tab_sorting('Participants', 'TC03_GC_Verify_Participants_Tab_Sorting')
    gc.assert_no_failures()
