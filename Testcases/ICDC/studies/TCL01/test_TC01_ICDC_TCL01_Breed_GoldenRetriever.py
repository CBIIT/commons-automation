"""Open Explore for study TCL01, filter Breed GoldenRetriever, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC01_ICDC_TCL01_Breed-GoldenRetriever.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC01_ICDC_TCL01_Breed_GoldenRetriever(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-TCL01')
    icdc.select_filter("Cases/Breed", 'GoldenRetr')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
