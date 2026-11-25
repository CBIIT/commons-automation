"""TC06_ICDC_OSA01_StageOfDisease-II — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_OSA01_StageOfDisease_II(icdc):
    icdc.load_query_file('TC06_ICDC_OSA01_StageOfDisease-II.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA01')
    icdc.select_filter('Cases/StageOfDisease', '2')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
