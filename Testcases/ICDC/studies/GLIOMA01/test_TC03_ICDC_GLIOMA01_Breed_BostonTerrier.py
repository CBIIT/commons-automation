"""Open Explore for study GLIOMA01, filter Breed BostonTerrier, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC03_ICDC_GLIOMA01_Breed-BostonTerrier.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC03_ICDC_GLIOMA01_Breed_BostonTerrier(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-GLIOMA')
    icdc.select_filter("Cases/Breed", 'Boston')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
