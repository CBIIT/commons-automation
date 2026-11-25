"""TC07_Bento_arm-d_PRStatus-NotReported — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC07_Bento_arm_d_PRStatus_NotReported(bento):
    bento.load_query_file('TC07_Bento_arm-d_PRStatus-NotReported.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.select_filter('Filter/PRStatus', 'NotReported')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
