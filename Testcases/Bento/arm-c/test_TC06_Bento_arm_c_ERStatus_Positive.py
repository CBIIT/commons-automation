"""TC06_Bento_arm-c_ERStatus-Positive — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC06_Bento_arm_c_ERStatus_Positive(bento):
    bento.load_query_file('TC06_Bento_arm-c_ERStatus-Positive.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'C')
    bento.select_filter('Filter/ERStatus', 'Positive')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
