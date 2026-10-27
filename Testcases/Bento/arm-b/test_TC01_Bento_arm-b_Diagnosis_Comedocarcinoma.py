"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and Diagnosis Comedocarcinoma, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC01_Bento_arm_b_Diagnosis_Comedocarcinoma(bento):
    bento.load_query_file("TC01_Bento_arm-b_Diagnosis-Comedocarcinoma.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/Diagnosis", "Comedocarcinoma")  # Diagnosis = Comedocarcinoma
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
