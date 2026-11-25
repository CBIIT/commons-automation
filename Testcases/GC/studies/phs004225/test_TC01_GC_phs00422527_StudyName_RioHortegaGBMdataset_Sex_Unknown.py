"""TC01_GC_phs00422527_StudyName-RioHortegaGBMdataset_Sex-Unknown — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs00422527_StudyName_RioHortegaGBMdataset_Sex_Unknown(gc):
    gc.load_query_file('TC01_GC_phs00422527_StudyName-RioHortegaGBMdataset_Sex-Unknown.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs004225')
    gc.select_filter('StudyFacet/StudyName', 'CDS-Study-RioHortegaGBMdataset')
    gc.select_filter('DemographicsFacet/Sex', 'Unknown')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Files')
    gc.assert_no_failures()
