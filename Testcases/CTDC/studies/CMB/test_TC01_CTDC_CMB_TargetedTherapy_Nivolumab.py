"""Open Explore, select study CMB and Participants Targeted Therapy Nivolumab, then compare stat bar and all result tabs to TSV queries."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC01_CTDC_CMB_TargetedTherapy_Nivolumab(ctdc):
    ctdc.load_query_file("TC01_CTDC_CMB_TargetedTherapy-Nivolumab.xlsx")
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_study("CMB")
    ctdc.select_filter("Participants/TargetedTherapy", "Z1D")
    ctdc.read_statbar()
    ctdc.verify_tab("Participants")
    ctdc.verify_tab("Biospecimens")
    ctdc.verify_tab("Files")
    ctdc.verify_tab("Study Files")
    ctdc.assert_no_failures()
