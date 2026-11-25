"""TC02_ICDC_OSA01_Biobank-CCOGC — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC02_ICDC_OSA01_Biobank_CCOGC(icdc):
    icdc.load_query_file('TC02_ICDC_OSA01_Biobank-CCOGC.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA01')
    icdc.select_filter('Cases/Biobank', 'CCOGC')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
