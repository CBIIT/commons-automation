"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and PR Status Not Reported, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC07_Bento_arm_b_PRStatus_NotReported(bento):
    bento.load_query_file("TC07_Bento_arm-b_PRStatus-NotReported.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/PRStatus", "NotReported")  # PR Status = Not Reported
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
