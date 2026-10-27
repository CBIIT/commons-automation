"""Open Explore, Arm D (D: RS > 25, assigned to chemo +) and File Type bam, then compare stat bar and Cases / Samples / Files tabs to expected queries."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC14_Bento_arm_d_FileType_bam(bento):
    bento.load_query_file("TC14_Bento_arm-d_FileType-bam.xlsx")
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter("Filter/Arm", "D")  # D: RS > 25, assigned to chemo +
    bento.select_filter("Filter/FileType", "Bam")  # File Type = bam
    bento.read_statbar()
    bento.verify_tab("Cases")
    bento.verify_tab("Samples")
    bento.verify_tab("Files")
    bento.assert_no_failures()
