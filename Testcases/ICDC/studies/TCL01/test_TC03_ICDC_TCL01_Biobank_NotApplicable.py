"""Open Explore for study TCL01, filter Biobank NotApplicable, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC03_ICDC_TCL01_Biobank-NotApplicable.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_TCL01_Biobank_NotApplicable(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-TCL01')
    icdc.select_filter("Cases/Biobank", 'NotApplicable')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
