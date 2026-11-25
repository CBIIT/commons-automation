"""TC04_ICDC_MGT01_Diagnosis-MammaryCancer — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC04_ICDC_MGT01_Diagnosis_MammaryCancer(icdc):
    icdc.load_query_file('TC04_ICDC_MGT01_Diagnosis-MammaryCancer.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-MGT01')
    icdc.select_filter('Cases/Diagnosis', 'MammaryCancer')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
