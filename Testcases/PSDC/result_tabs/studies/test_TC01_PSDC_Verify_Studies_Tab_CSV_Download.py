"""TC01_PSDC_Verify_Studies_Tab_CSV_Download — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC01_PSDC_Verify_Studies_Tab_CSV_Download(psdc):
    psdc.load_query_file('PSDC_ResultTabDownloads.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.result_tabs.download('Studies', 'CSV', 'TC01_PSDC_Verify_Studies_Tab_CSV_Download')
    psdc.result_tabs.verify_download('Studies', 'CSV')
    psdc.assert_no_failures()
