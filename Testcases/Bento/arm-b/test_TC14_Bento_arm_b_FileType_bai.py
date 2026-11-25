"""TC14_Bento_arm-b_FileType-bai — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC14_Bento_arm_b_FileType_bai(bento):
    bento.load_query_file('TC14_Bento_arm-b_FileType-bai.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/FileType', 'Bai')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
