"""TC05_Bento_arm-c_TumorGrade-LowGrade — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC05_Bento_arm_c_TumorGrade_LowGrade(bento):
    bento.load_query_file('TC05_Bento_arm-c_TumorGrade-LowGrade.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'C')
    bento.select_filter('Filter/TumorGrade', 'Low')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
