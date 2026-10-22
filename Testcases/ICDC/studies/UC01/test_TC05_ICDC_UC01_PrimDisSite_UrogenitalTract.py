"""Open Explore for study UC01, filter PrimDisSite UrogenitalTract, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC05_ICDC_UC01_PrimDisSite-UrogenitalTract.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC05_ICDC_UC01_PrimDisSite_UrogenitalTract(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-UC01')
    icdc.select_filter("Cases/PrimaryDiseaseSite", 'UrogenitalTract')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
