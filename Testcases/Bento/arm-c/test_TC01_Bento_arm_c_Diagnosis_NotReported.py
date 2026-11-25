"""TC01_Bento_arm-c_Diagnosis-NotReported — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_Bento_arm_c_Diagnosis_NotReported(bento):
    bento.load_query_file('TC01_Bento_arm-c_Diagnosis-NotReported.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'C')
    bento.select_filter('Filter/Diagnosis', 'NotReported')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
