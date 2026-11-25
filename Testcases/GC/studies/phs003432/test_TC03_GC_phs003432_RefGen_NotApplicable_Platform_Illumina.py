"""TC03_GC_phs003432_RefGen_NotApplicable_Platform-Illumina — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs003432_RefGen_NotApplicable_Platform_Illumina(gc):
    gc.load_query_file('TC03_GC_phs003432_RefGen_NotApplicable_Platform-Illumina.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs003432')
    gc.select_filter('GenomicFacet/Platform', 'ILLUMINA')
    gc.select_filter('GenomicFacet/LibrarySource', 'GenomicSingleCell')
    gc.select_filter('GenomicFacet/ReferenceGenomeAssembly', 'NotApplicable')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
