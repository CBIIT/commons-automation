"""TC04_ICDC_GLIOMA01_Diagnosis-Glioma — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC04_ICDC_GLIOMA01_Diagnosis_Glioma(icdc):
    icdc.load_query_file('TC04_ICDC_GLIOMA01_Diagnosis-Glioma.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-GLIOMA')
    icdc.select_filter('Cases/Diagnosis', 'Glioma')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
