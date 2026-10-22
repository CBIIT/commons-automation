"""Open Explore for study TCL01, filter Diagnosis BCellLymphoma, then compare stat bar and result tabs to DB queries."""

import pytest

_INPUT = "TC04_ICDC_TCL01_Diagnosis-BCellLymphoma.xlsx"


@pytest.mark.icdc
@pytest.mark.regression
def test_TC04_ICDC_TCL01_Diagnosis_BCellLymphoma(icdc):
    icdc.load_query_file(_INPUT)
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-TCL01')
    icdc.select_filter("Cases/Diagnosis", 'BCellLymphoma')
    icdc.read_statbar()
    icdc.verify_tab("Cases")
    icdc.verify_tab("Samples")
    icdc.verify_tab("Case Files")
    icdc.verify_tab("Study Files")
    icdc.assert_no_failures()
