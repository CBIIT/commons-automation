"""TC05_GC_phs001524_LibraryStrategy-TgtCap_LibrarySource-Genomic — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs001524_LibraryStrategy_TgtCap_LibrarySource_Genomic(gc):
    gc.load_query_file('TC05_GC_phs001524_LibraryStrategy-TgtCap_LibrarySource-Genomic.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001524')
    gc.select_filter('GenomicFacet/LibraryStrategy', 'TargetedCapture')
    gc.select_filter('GenomicFacet/LibrarySource', 'Genomic')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
