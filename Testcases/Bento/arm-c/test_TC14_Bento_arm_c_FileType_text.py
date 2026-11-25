"""TC14_Bento_arm-c_FileType-text — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC14_Bento_arm_c_FileType_text(bento):
    bento.load_query_file('TC14_Bento_arm-c_FileType-text.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'C')
    bento.select_filter('Filter/FileType', 'Text')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
