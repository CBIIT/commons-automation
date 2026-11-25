"""TC02_ICDC_COTC026_Breed-SaintBernard — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC02_ICDC_COTC026_Breed_SaintBernard(icdc):
    icdc.load_query_file('TC02_ICDC_COTC026_Breed-SaintBernard.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTC026')
    icdc.select_filter('Cases/Breed', 'SaintBnd')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
