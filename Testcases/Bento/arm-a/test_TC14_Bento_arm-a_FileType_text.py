"""Open Explore, Arm A (A: RS 0-10, assigned endocrine therapy alone) and File Type text, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC14_Bento_arm_a_FileType_text(bento):
    bento.load_query_file("TC14_Bento_arm-a_FileType-text.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "A")  # A: RS 0-10, assigned endocrine therapy alone
    bento.select_filter("Filter/FileType", "Text")  # File Type = text
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
