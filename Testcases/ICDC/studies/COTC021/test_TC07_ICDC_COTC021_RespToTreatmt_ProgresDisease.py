"""Open Explore for study COTC021, filter RespToTreatmt ProgresDisease, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC07_ICDC_COTC021_RespToTreatmt-ProgresDisease.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC07_ICDC_COTC021_RespToTreatmt_ProgresDisease(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTC021')
    icdc.select_filter("Cases/ResponseToTreatment", 'ProgrDisease')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
