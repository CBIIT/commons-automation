"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and Tumor Grade Intermediate Grade, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC05_Bento_arm_b_TumorGrade_IntermediateGrade(bento):
    bento.load_query_file("TC05_Bento_arm-b_TumorGrade-IntermediateGrade.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/TumorGrade", "Intermediate")  # Tumor Grade = Intermediate Grade
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
