"""TC06_ICDC_UBC03_Diagnosis-HealthyControl — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_UBC03_Diagnosis_HealthyControl(icdc):
    icdc.load_query_file('TC06_ICDC_UBC03_Diagnosis-HealthyControl.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-UBC03')
    icdc.select_filter('Cases/Diagnosis', 'HealthyControl')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
