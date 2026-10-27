"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Endocrine Therapy AI, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC08_Bento_arm_a_EndocrineTherapy_AI(bento):
    bento.load_query_file("TC08_Bento_arm-a_EndocrineTherapy-AI.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/EndocrineTherapy", "AI")  # Endocrine Therapy = AI
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
