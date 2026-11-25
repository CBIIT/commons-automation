"""TC06_Bento_arm-b_ERStatus-Negative — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC06_Bento_arm_b_ERStatus_Negative(bento):
    bento.load_query_file('TC06_Bento_arm-b_ERStatus-Negative.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/ERStatus', 'Negative')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
