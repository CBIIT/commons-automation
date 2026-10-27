"""Open Explore, Arm B (B: RS 11-25, randomized to endocrine therapy alone) and Endocrine Therapy None, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC08_Bento_arm_b_EndocrineTherapy_None(bento):
    bento.load_query_file("TC08_Bento_arm-b_EndocrineTherapy-None.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "B")  # B: RS 11-25, randomized to endocrine therapy alone
    bento.select_filter("Filter/EndocrineTherapy", "None")  # Endocrine Therapy = None
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
