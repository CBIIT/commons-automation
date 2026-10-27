"""Open Explore, Arm C (C: RS 11-25, randomized to chemo + endocrine therapy) and Tumor Grade Low Grade, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC05_Bento_arm_c_TumorGrade_LowGrade(bento):
    bento.load_query_file("TC05_Bento_arm-c_TumorGrade-LowGrade.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "C")  # C: RS 11-25, randomized to chemo + endocrine therapy
    bento.select_filter("Filter/TumorGrade", "Low")  # Tumor Grade = Low Grade
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
