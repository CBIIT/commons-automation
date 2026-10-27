"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Tumor Grade High Grade, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC05_Bento_arm_a_TumorGrade_HighGrade(bento):
    bento.load_query_file("TC05_Bento_arm-a_TumorGrade-HighGrade.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/TumorGrade", "High")  # Tumor Grade = High Grade
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
