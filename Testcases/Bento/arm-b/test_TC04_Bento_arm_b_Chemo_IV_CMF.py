"""TC04_Bento_arm-b_Chemo-IV_CMF — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC04_Bento_arm_b_Chemo_IV_CMF(bento):
    bento.load_query_file('TC04_Bento_arm-b_Chemo-IV_CMF.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/Chemotherapy', 'IVCMF-3WkCycle')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
