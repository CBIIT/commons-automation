"""TC01_CTDC_CMB_Diagnosis-ColorctlCarcin — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_CTDC_CMB_Diagnosis_ColorctlCarcin(ctdc):
    ctdc.load_query_file('TC01_CTDC_CMB_Diagnosis-ColorctlCarcin.xlsx')
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_study('CMB')
    ctdc.select_filter('Participants/Diagnosis', 'ColorectalCarcin')
    ctdc.read_statbar()
    ctdc.verify_tab('Participants')
    ctdc.verify_tab('Biospecimens')
    ctdc.verify_tab('Files')
    ctdc.verify_tab('Study Files')
    ctdc.assert_no_failures()
