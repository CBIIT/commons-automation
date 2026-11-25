"""TC07_ICDC_GLIOMA01_RespToTreatmt-NotDetermined — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC07_ICDC_GLIOMA01_RespToTreatmt_NotDetermined(icdc):
    icdc.load_query_file('TC07_ICDC_GLIOMA01_RespToTreatmt-NotDetermined.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-GLIOMA')
    icdc.select_filter('Cases/ResponseToTreatment', 'NotDetermined')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
