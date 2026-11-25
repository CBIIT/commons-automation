"""TC05_GC_phs001819_LibraryStrategy-WXS_LibrarySelection-Random — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs001819_LibraryStrategy_WXS_LibrarySelection_Random(gc):
    gc.load_query_file('TC05_GC_phs001819_LibraryStrategy-WXS_LibrarySelection-Random.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001819')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'WXS')
    gc.select_filter('GenomicFacet/LibrarySelection', 'Random')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
