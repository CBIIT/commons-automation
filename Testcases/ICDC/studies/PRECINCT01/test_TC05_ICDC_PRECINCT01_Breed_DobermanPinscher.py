"""TC05_ICDC_PRECINCT01_Breed-DobermanPinscher — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC05_ICDC_PRECINCT01_Breed_DobermanPinscher(icdc):
    icdc.load_query_file('TC05_ICDC_PRECINCT01_Breed-DobermanPinscher.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-PRECINCT01')
    icdc.select_filter('Cases/Breed', 'DobrmnPinsh')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
