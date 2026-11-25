"""TC07_Bento_arm-b_PRStatus-NotReported — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC07_Bento_arm_b_PRStatus_NotReported(bento):
    bento.load_query_file('TC07_Bento_arm-b_PRStatus-NotReported.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/PRStatus', 'NotReported')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
