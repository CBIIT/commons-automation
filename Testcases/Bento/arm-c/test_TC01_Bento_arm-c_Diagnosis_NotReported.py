"""Open Explore, Arm C (C: RS 11-25, randomized to chemo + endocrine therapy) and Diagnosis Not Reported, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC01_Bento_arm_c_Diagnosis_NotReported(bento):
    bento.load_query_file("TC01_Bento_arm-c_Diagnosis-NotReported.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "C")  # C: RS 11-25, randomized to chemo + endocrine therapy
    bento.select_filter("Filter/Diagnosis", "NotReported")  # Diagnosis = Not Reported
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
