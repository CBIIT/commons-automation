"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and File Association sample, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC13_Bento_arm_b_FileAssoc_Sample(bento):
    bento.load_query_file("TC13_Bento_arm-b_FileAssoc-Sample.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/FileAssociation", "Sample")  # File Association = sample
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
