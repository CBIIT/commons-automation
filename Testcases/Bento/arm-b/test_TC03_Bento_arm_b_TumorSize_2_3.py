"""TC03_Bento_arm-b_TumorSize-2-3 — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC03_Bento_arm_b_TumorSize_2_3(bento):
    bento.load_query_file('TC03_Bento_arm-b_TumorSize-2-3.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/TumorSize', '2_to_3')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
