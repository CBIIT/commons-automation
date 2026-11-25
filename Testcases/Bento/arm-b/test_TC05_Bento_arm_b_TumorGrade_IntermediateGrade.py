"""TC05_Bento_arm-b_TumorGrade-IntermediateGrade — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC05_Bento_arm_b_TumorGrade_IntermediateGrade(bento):
    bento.load_query_file('TC05_Bento_arm-b_TumorGrade-IntermediateGrade.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/TumorGrade', 'Intermediate')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
