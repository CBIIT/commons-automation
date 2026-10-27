"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and Age 10–30 years, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC10_Bento_arm_a_Age_10_to_30(bento):
    bento.load_query_file("TC10_Bento_arm-a_Age-10_to_30.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.set_age_range(10, 30)  # Age = 10–30 years
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
