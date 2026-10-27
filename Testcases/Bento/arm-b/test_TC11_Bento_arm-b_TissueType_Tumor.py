"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and Tissue Type Tumor, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC11_Bento_arm_b_TissueType_Tumor(bento):
    bento.load_query_file("TC11_Bento_arm-b_TissueType-Tumor.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/TissueType", "Tumor")  # Tissue Type = Tumor
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
