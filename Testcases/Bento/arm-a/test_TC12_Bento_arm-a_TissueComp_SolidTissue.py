"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Tissue Composition Solid Tissue, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC12_Bento_arm_a_TissueComp_SolidTissue(bento):
    bento.load_query_file("TC12_Bento_arm-a_TissueComp-SolidTissue.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/TissueComposition", "SolidTissue")  # Tissue Composition = Solid Tissue
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
