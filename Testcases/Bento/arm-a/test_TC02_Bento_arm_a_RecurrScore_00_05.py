"""TC02_Bento_arm-a_RecurrScore-00-05 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
@pytest.mark.smoke
def test_TC02_Bento_arm_a_RecurrScore_00_05(bento):
    bento.load_query_file('TC02_Bento_arm-a_RecurrScore-00-05.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/Recurrence Score', '00_to_05')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
