"""TC11_Bento_arm-b_TissueType-Tumor — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.quickrun
@pytest.mark.regression
@pytest.mark.smoke
def test_TC11_Bento_arm_b_TissueType_Tumor(bento):
    bento.load_query_file('TC11_Bento_arm-b_TissueType-Tumor.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/TissueType', 'Tumor')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
