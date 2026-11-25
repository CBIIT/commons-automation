"""TC08_Bento_arm-b_EndocrineTherapy-None — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC08_Bento_arm_b_EndocrineTherapy_None(bento):
    bento.load_query_file('TC08_Bento_arm-b_EndocrineTherapy-None.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/EndocrineTherapy', 'None')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
