"""TC03_ICDC_OSA01_Breed-Greyhound — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_OSA01_Breed_Greyhound(icdc):
    icdc.load_query_file('TC03_ICDC_OSA01_Breed-Greyhound.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA01')
    icdc.select_filter('Cases/Breed', 'Greyhnd')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
