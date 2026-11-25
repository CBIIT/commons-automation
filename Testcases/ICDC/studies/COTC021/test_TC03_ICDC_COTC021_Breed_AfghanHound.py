"""TC03_ICDC_COTC021_Breed-AfghanHound — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC03_ICDC_COTC021_Breed_AfghanHound(icdc):
    icdc.load_query_file('TC03_ICDC_COTC021_Breed-AfghanHound.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTC021')
    icdc.select_filter('Cases/Breed', 'AfgHound')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
