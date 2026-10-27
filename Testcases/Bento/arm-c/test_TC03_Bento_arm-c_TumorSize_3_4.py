"""Open Explore, Arm C (C: RS 11-25, randomized to chemo + endocrine therapy) and Tumor Size (3,4], then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC03_Bento_arm_c_TumorSize_3_4(bento):
    bento.load_query_file("TC03_Bento_arm-c_TumorSize-3-4.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "C")  # C: RS 11-25, randomized to chemo + endocrine therapy
    bento.select_filter("Filter/TumorSize", "3_to_4")  # Tumor Size = (3,4]
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
