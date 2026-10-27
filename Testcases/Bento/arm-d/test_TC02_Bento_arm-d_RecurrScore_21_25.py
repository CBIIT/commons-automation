"""Open Explore, Arm D (D: RS > 25, assigned to chemo +) and Recurrence Score 21–25, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC02_Bento_arm_d_RecurrScore_21_25(bento):
    bento.load_query_file("TC02_Bento_arm-d_RecurrScore-21-25.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "D")  # D: RS > 25, assigned to chemo +
    bento.select_filter("Filter/Recurrence Score", "21_to_25")  # Recurrence Score = 21–25
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
