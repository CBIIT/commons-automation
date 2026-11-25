"""TC04_ICDC_UBC03_Breed-ScottishTerrier — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC04_ICDC_UBC03_Breed_ScottishTerrier(icdc):
    icdc.load_query_file('TC04_ICDC_UBC03_Breed-ScottishTerrier.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-UBC03')
    icdc.select_filter('Cases/Breed', 'ScottTerr')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
