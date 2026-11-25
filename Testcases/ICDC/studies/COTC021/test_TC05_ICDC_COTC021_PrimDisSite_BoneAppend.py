"""TC05_ICDC_COTC021_PrimDisSite-BoneAppend — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC05_ICDC_COTC021_PrimDisSite_BoneAppend(icdc):
    icdc.load_query_file('TC05_ICDC_COTC021_PrimDisSite-BoneAppend.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTC021')
    icdc.select_filter('Cases/PrimaryDiseaseSite', 'BoneApendicular')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
