"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and Recurrence Score 11–15, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC02_Bento_arm_b_RecurrScore_11_15(bento):
    bento.load_query_file("TC02_Bento_arm-b_RecurrScore-11-15.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/Recurrence Score", "11_to_15")  # Recurrence Score = 11–15
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
