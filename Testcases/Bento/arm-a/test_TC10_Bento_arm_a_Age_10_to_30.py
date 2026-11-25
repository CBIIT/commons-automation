"""TC10_Bento_arm-a_Age-10_to_30 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC10_Bento_arm_a_Age_10_to_30(bento):
    bento.load_query_file('TC10_Bento_arm-a_Age-10_to_30.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.set_age_range(10, 30)
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
