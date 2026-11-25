"""TC05_GC_phs001713_LibrarySource-Genomic_LibraryLayout-PairedEnd — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC05_GC_phs001713_LibrarySource_Genomic_LibraryLayout_PairedEnd(gc):
    gc.load_query_file('TC05_GC_phs001713_LibrarySource-Genomic_LibraryLayout-PairedEnd.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001713')
    gc.select_filter('GenomicFacet/LibrarySource', 'Genomic')
    gc.select_filter('GenomicFacet/LibraryLayout', 'Pairedend')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
