"""TC10_Bento_arm-b_Age-31_to_45 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC10_Bento_arm_b_Age_31_to_45(bento):
    bento.load_query_file('TC10_Bento_arm-b_Age-31_to_45.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.set_age_range(31, 45)
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
