"""TC06_ICDC_ORGANOIDS01_StageOfDisease-T2N0M0 — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_ORGANOIDS01_StageOfDisease_T2N0M0(icdc):
    icdc.load_query_file('TC06_ICDC_ORGANOIDS01_StageOfDisease-T2N0M0.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-ORGANOIDS01')
    icdc.select_filter('Cases/StageOfDisease', 'T2N0M0')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
