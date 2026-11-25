"""TC02_Bento_arm-c_RecurrScore-16-20 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
@pytest.mark.smoke
def test_TC02_Bento_arm_c_RecurrScore_16_20(bento):
    bento.load_query_file('TC02_Bento_arm-c_RecurrScore-16-20.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'C')
    bento.select_filter('Filter/Recurrence Score', '16_to_20')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
