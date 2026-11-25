"""TC01_GC_Verify_Participants_Tab_CSV_Download — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_Verify_Participants_Tab_CSV_Download(gc):
    gc.load_query_file('GC_ResultTabDownloads.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs000720')
    gc.select_filter('FilesFacet/FileType', 'hdf5')
    gc.result_tabs.download('Participants', 'CSV', 'TC01_GC_Verify_Participants_Tab_CSV_Download')
    gc.result_tabs.verify_download('Participants', 'CSV')
    gc.assert_no_failures()
