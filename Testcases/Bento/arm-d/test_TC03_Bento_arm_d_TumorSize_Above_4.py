"""TC03_Bento_arm-d_TumorSize-Above_4 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC03_Bento_arm_d_TumorSize_Above_4(bento):
    bento.load_query_file('TC03_Bento_arm-d_TumorSize-Above_4.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.select_filter('Filter/TumorSize', 'Above_4')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
