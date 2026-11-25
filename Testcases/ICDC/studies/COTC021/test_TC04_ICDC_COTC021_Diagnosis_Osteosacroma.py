"""TC04_ICDC_COTC021_Diagnosis-Osteosacroma — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC04_ICDC_COTC021_Diagnosis_Osteosacroma(icdc):
    icdc.load_query_file('TC04_ICDC_COTC021_Diagnosis-Osteosacroma.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTC021')
    icdc.select_filter('Cases/Diagnosis', 'OsteoSarcoma')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
