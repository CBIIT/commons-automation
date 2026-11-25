"""TC02_Bento_arm-d_RecurrScore-26-30 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
@pytest.mark.smoke
def test_TC02_Bento_arm_d_RecurrScore_26_30(bento):
    bento.load_query_file('TC02_Bento_arm-d_RecurrScore-26-30.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.select_filter('Filter/Recurrence Score', '26_to_30')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
