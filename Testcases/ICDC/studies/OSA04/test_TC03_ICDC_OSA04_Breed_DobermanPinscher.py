"""Open Explore for study OSA04, filter Breed DobermanPinscher, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC03_ICDC_OSA04_Breed-DobermanPinscher.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_OSA04_Breed_DobermanPinscher(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA04')
    icdc.select_filter("Cases/Breed", 'DobrmnPinsh')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
