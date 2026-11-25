"""TC02_ICDC_UC01_Biobank-NotApplicable — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC02_ICDC_UC01_Biobank_NotApplicable(icdc):
    icdc.load_query_file('TC02_ICDC_UC01_Biobank-NotApplicable.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-UC01')
    icdc.select_filter('Cases/Biobank', 'NotApplicable')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
