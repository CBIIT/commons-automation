"""TC01_Bento_arm-d_Diagnosis-TubularCarcinoma — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_Bento_arm_d_Diagnosis_TubularCarcinoma(bento):
    bento.load_query_file('TC01_Bento_arm-d_Diagnosis-TubularCarcinoma.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'D')
    bento.select_filter('Filter/Diagnosis', 'TubularCarcinoma')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
