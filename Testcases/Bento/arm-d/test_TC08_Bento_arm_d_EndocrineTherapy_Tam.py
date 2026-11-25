"""TC08_Bento_arm-d_EndocrineTherapy-Tam — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC08_Bento_arm_d_EndocrineTherapy_Tam(bento):
    bento.load_query_file('TC08_Bento_arm-d_EndocrineTherapy-Tam.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.select_filter('Filter/EndocrineTherapy', 'Tam')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
