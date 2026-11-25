"""TC03_ICDC_Verify_Cases_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_Verify_Cases_Tab_Sorting(icdc):
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_filter('Cases/Study', 'Canine_Filter_Study-COTC021')
    icdc.select_filter('Cases/Breed', 'BernMtnDog')
    icdc.verify_result_tab_sorting('Cases', 'TC03_ICDC_Verify_Cases_Tab_Sorting')
    icdc.assert_no_failures()
