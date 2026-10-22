"""Open Explore for study OSA02, filter RespToTreatmt NotApplicable, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC07_ICDC_OSA02_RespToTreatmt-NotApplicable.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC07_ICDC_OSA02_RespToTreatmt_NotApplicable(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA02')
    icdc.select_filter("Cases/ResponseToTreatment", 'NotApplicable')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
