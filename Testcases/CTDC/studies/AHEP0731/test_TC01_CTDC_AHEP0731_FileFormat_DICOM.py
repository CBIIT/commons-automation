"""Open Explore, select study AHEP0731 and Files File Format DICOM, then compare stat bar and all result tabs to TSV queries."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC01_CTDC_AHEP0731_FileFormat_DICOM(ctdc):
    ctdc.load_query_file("TC01_CTDC_AHEP0731_FileFormat-DICOM.xlsx")
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_study("AHEP0731")
    ctdc.select_filter("Files/FileFormat", "DICOM")
    ctdc.read_statbar()
    ctdc.verify_tab("Participants")
    ctdc.verify_tab("Biospecimens")
    ctdc.verify_tab("Files")
    ctdc.verify_tab("Study Files")
    ctdc.assert_no_failures()
