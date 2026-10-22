"""Open Explore for study GLIOMA01, filter StageOfDisease Unknown, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC06_ICDC_GLIOMA01_StageOfDisease-Unknown.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_GLIOMA01_StageOfDisease_Unknown(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-GLIOMA')
    icdc.select_filter("Cases/StageOfDisease", 'Unknown')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
