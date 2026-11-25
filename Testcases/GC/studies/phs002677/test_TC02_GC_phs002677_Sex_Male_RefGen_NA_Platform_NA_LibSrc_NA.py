"""TC02_GC_phs002677_Sex_Male_RefGen_NA_Platform-NA_LibSrc-NA — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs002677_Sex_Male_RefGen_NA_Platform_NA_LibSrc_NA(gc):
    gc.load_query_file('TC02_GC_phs002677_Sex_Male_RefGen_NA_Platform-NA_LibSrc-NA.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002677')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('GenomicFacet/Platform', 'NotApplicable')
    gc.select_filter('GenomicFacet/LibrarySource', 'NotApplicable')
    gc.select_filter('GenomicFacet/ReferenceGenomeAssembly', 'NotApplicable')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.assert_no_failures()
