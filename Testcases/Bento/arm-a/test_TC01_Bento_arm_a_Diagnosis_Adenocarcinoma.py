"""TC01_Bento_arm-a_Diagnosis-Adenocarcinoma — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.quickrun
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_Bento_arm_a_Diagnosis_Adenocarcinoma(bento):
    bento.load_query_file('TC01_Bento_arm-a_Diagnosis-Adenocarcinoma.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/Diagnosis', 'Adenocarcinoma')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
