"""TC05_ICDC_STS01_Breed-Beagle — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC05_ICDC_STS01_Breed_Beagle(icdc):
    icdc.load_query_file('TC05_ICDC_STS01_Breed-Beagle.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-STS01')
    icdc.select_filter('Cases/Breed', 'Beagle')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
