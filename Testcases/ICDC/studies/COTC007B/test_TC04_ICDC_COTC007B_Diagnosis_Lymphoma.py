"""Open Explore for study COTC007B, filter Diagnosis Lymphoma, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC04_ICDC_COTC007B_Diagnosis-Lymphoma.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC04_ICDC_COTC007B_Diagnosis_Lymphoma(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-COTB')
    icdc.select_filter("Cases/Diagnosis", 'Lymphoma')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
