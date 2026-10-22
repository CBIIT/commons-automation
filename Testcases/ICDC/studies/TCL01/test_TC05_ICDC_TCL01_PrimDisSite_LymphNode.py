"""Open Explore for study TCL01, filter PrimDisSite LymphNode, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC05_ICDC_TCL01_PrimDisSite-LymphNode.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC05_ICDC_TCL01_PrimDisSite_LymphNode(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-TCL01')
    icdc.select_filter("Cases/PrimaryDiseaseSite", 'LymphNode')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
