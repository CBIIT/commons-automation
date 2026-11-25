"""TC04_Bento_arm-a_Chemo-None — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC04_Bento_arm_a_Chemo_None(bento):
    bento.load_query_file('TC04_Bento_arm-a_Chemo-None.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/Chemotherapy', 'None')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
