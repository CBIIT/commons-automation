"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Chemotherapy None, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC04_Bento_arm_a_Chemo_None(bento):
    bento.load_query_file("TC04_Bento_arm-a_Chemo-None.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/Chemotherapy", "None")  # Chemotherapy = None
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
