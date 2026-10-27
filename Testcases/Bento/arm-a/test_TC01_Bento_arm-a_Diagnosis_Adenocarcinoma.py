"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Diagnosis Adenocarcinoma, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC01_Bento_arm_a_Diagnosis_Adenocarcinoma(bento):
    bento.load_query_file("TC01_Bento_arm-a_Diagnosis-Adenocarcinoma.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/Diagnosis", "Adenocarcinoma")  # Diagnosis = Adenocarcinoma
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
