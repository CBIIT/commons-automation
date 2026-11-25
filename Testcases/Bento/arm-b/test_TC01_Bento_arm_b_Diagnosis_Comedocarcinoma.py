"""TC01_Bento_arm-b_Diagnosis-Comedocarcinoma — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_Bento_arm_b_Diagnosis_Comedocarcinoma(bento):
    bento.load_query_file('TC01_Bento_arm-b_Diagnosis-Comedocarcinoma.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/Diagnosis', 'Comedocarcinoma')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
