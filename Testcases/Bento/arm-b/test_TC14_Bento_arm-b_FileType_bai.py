"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and File Type bai, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC14_Bento_arm_b_FileType_bai(bento):
    bento.load_query_file("TC14_Bento_arm-b_FileType-bai.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/FileType", "Bai")  # File Type = bai
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
