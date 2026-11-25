"""TC01_CTDC_AHEP0731_FileType-RadiologyImaging — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_CTDC_AHEP0731_FileType_RadiologyImaging(ctdc):
    ctdc.load_query_file('TC01_CTDC_AHEP0731_FileType-RadiologyImaging.xlsx')
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_study('AHEP0731')
    ctdc.select_filter('Files/FileType', 'RadiologyImaging')
    ctdc.read_statbar()
    ctdc.verify_tab('Participants')
    ctdc.verify_tab('Biospecimens')
    ctdc.verify_tab('Files')
    ctdc.verify_tab('Study Files')
    ctdc.assert_no_failures()
