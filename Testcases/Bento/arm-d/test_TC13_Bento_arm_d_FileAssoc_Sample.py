"""TC13_Bento_arm-d_FileAssoc-Sample — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC13_Bento_arm_d_FileAssoc_Sample(bento):
    bento.load_query_file('TC13_Bento_arm-d_FileAssoc-Sample.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.select_filter('Filter/FileAssociation', 'Sample')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
