"""TC07_Bento_arm-a_PRStatus-Positive — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC07_Bento_arm_a_PRStatus_Positive(bento):
    bento.load_query_file('TC07_Bento_arm-a_PRStatus-Positive.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/PRStatus', 'Positive')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
