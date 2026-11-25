"""TC01_CTDC_Verify_Study_Files_Tab_CSV_Download — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC01_CTDC_Verify_Study_Files_Tab_CSV_Download(ctdc):
    ctdc.load_query_file('CTDC_ResultTabDownloads.xlsx')
    ctdc.accept_banner()
    ctdc.open_explore()
    ctdc.select_filter('Studies/Study', 'CMB')
    ctdc.result_tabs.download('Study Files', 'CSV', 'TC01_CTDC_Verify_Study_Files_Tab_CSV_Download')
    ctdc.result_tabs.verify_download('Study Files', 'CSV')
    ctdc.assert_no_failures()
