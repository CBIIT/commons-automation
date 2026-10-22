"""Open Explore for study COTC026, filter Breed SaintBernard, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC02_ICDC_COTC026_Breed-SaintBernard.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC02_ICDC_COTC026_Breed_SaintBernard(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTC026')
    icdc.select_filter("Cases/Breed", 'SaintBnd')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
