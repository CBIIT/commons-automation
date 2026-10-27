"""Open Explore, Arm D (D: RS > 25, assigned to chemo +) and Chemotherapy TC (3 week cycles), then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC04_Bento_arm_d_Chemo_TC3Wk(bento):
    bento.load_query_file("TC04_Bento_arm-d_Chemo-TC.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "D")  # D: RS > 25, assigned to chemo +
    bento.select_filter("Filter/Chemotherapy", "TC-3WkCycle")  # Chemotherapy = TC (3 week cycles, includes any taxane with cyclophosphamide)
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
