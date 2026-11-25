"""TC03_GC_phs002677_Sex_Male_LibSel-NA_LibLay-NA_InstMod-NA — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC03_GC_phs002677_Sex_Male_LibSel_NA_LibLay_NA_InstMod_NA(gc):
    gc.load_query_file('TC03_GC_phs002677_Sex_Male_LibSel-NA_LibLay-NA_InstMod-NA.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002677')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('GenomicFacet/LibrarySelection', 'NotApplicable')
    gc.select_filter('GenomicFacet/LibraryLayout', 'NotApplicable')
    gc.select_filter('GenomicFacet/InstrumentModel', 'NotApplicable')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
