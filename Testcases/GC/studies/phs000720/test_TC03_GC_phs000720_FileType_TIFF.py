"""TC03_GC_phs000720_FileType_TIFF — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC03_GC_phs000720_FileType_TIFF(gc):
    gc.load_query_file('TC03_GC_phs000720_FileType_TIFF.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs000720')
    gc.select_filter('FilesFacet/FileType', 'tiff')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
