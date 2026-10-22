"""Open Explore for study OSA01, filter PrimDisSite BoneAppendicular, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC05_ICDC_OSA01_PrimDisSite-BoneAppendicular.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC05_ICDC_OSA01_PrimDisSite_BoneAppendicular(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA01')
    icdc.select_filter("Cases/PrimaryDiseaseSite", 'BoneApendicular')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
