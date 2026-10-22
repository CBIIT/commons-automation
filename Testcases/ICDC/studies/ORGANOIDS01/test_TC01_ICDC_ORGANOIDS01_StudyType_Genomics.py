"""Open Explore for study ORGANOIDS01, filter StudyType Genomics, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC01_ICDC_ORGANOIDS01_StudyType-Genomics.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC01_ICDC_ORGANOIDS01_StudyType_Genomics(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-ORGANOIDS01')
    icdc.select_filter("Cases/StudyType", 'Canine_Filter_StudyType-Genomics')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
