"""TC05_Bento_arm-a_TumorGrade-HighGrade — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC05_Bento_arm_a_TumorGrade_HighGrade(bento):
    bento.load_query_file('TC05_Bento_arm-a_TumorGrade-HighGrade.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/TumorGrade', 'High')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
