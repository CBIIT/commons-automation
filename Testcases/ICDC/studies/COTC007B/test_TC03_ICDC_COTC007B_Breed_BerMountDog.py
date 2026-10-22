"""Open Explore for study COTC007B, filter Breed BerMountDog, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC03_ICDC_COTC007B_Breed-BerMountDog.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_COTC007B_Breed_BerMountDog(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTB')
    icdc.select_filter("Cases/Breed", 'BernMtnDog')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
