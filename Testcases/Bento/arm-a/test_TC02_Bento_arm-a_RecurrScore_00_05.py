"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Recurrence Score 0–5, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC02_Bento_arm_a_RecurrScore_00_05(bento):
    bento.load_query_file("TC02_Bento_arm-a_RecurrScore-00-05.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/Recurrence Score", "00_to_05")  # Recurrence Score = 0–5
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
