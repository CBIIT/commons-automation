"""TC10_Bento_arm-d_Age-61_to_75 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC10_Bento_arm_d_Age_61_to_75(bento):
    bento.load_query_file('TC10_Bento_arm-d_Age-61_to_75.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.set_age_range(61, 75)
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
