"""TC01_GC_phs0042256_StudyName-AntiPD1MELANOMA_StudyDataTypes-Imaging — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs0042256_StudyName_AntiPD1MELANOMA_StudyDataTypes_Imaging(gc):
    gc.load_query_file('TC01_GC_phs0042256_StudyName-AntiPD1MELANOMA_StudyDataTypes-Imaging.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs004225')
    gc.select_filter('StudyFacet/StudyName', 'CDS-Study-AntiPD1MELANOMA')
    gc.select_filter('StudyFacet/StudyDataTypes', 'Imaging')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Files')
    gc.assert_no_failures()
