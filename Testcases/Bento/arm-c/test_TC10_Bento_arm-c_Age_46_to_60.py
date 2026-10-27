"""Open Explore, Arm C (C: RS 11-25, randomized to chemo + endocrine therapy) and Age 46–60 years, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC10_Bento_arm_c_Age_46_to_60(bento):
    bento.load_query_file("TC10_Bento_arm-c_Age-46_to_60.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "C")  # C: RS 11-25, randomized to chemo + endocrine therapy
    bento.set_age_range(46, 60)  # Age = 46–60 years
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
