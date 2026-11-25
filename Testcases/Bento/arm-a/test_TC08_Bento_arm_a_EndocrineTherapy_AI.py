"""TC08_Bento_arm-a_EndocrineTherapy-AI — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC08_Bento_arm_a_EndocrineTherapy_AI(bento):
    bento.load_query_file('TC08_Bento_arm-a_EndocrineTherapy-AI.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/EndocrineTherapy', 'AI')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
