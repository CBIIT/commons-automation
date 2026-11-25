"""TC06_ICDC_OSA02_StageOfDisease-IIIb — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_OSA02_StageOfDisease_IIIb(icdc):
    icdc.load_query_file('TC06_ICDC_OSA02_StageOfDisease-IIIb.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA02')
    icdc.select_filter('Cases/StageOfDisease', '3b')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
