"""Open Explore for study NCATSCOP01, filter StageOfDisease V, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC06_ICDC_NCATSCOP01_StageOfDisease-V.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_NCATSCOP01_StageOfDisease_V(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-NCATS')
    icdc.select_filter("Cases/StageOfDisease", '5')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
