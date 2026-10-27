"""Open Explore, Arm C (C: RS 11-25, randomized to chemo + endocrine therapy) and File Type text, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC14_Bento_arm_c_FileType_text(bento):
    bento.load_query_file("TC14_Bento_arm-c_FileType-text.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "C")  # C: RS 11-25, randomized to chemo + endocrine therapy
    bento.select_filter("Filter/FileType", "Text")  # File Type = text
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
