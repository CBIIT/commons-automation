"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and Tumor Size (2,3], then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC03_Bento_arm_b_TumorSize_2_3(bento):
    bento.load_query_file("TC03_Bento_arm-b_TumorSize-2-3.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/TumorSize", "2_to_3")  # Tumor Size = (2,3]
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
