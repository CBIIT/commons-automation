"""TC01_ICDC_Verify_Cases_Tab_CSV_Download — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC01_ICDC_Verify_Cases_Tab_CSV_Download(icdc):
    icdc.load_query_file('ICDC_ResultTabDownloads.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_filter('Cases/Study', 'Canine_Filter_Study-COTC021')
    icdc.select_filter('Cases/Breed', 'BernMtnDog')
    icdc.result_tabs.download('Cases', 'CSV', 'TC01_ICDC_Verify_Cases_Tab_CSV_Download')
    icdc.result_tabs.verify_download('Cases', 'CSV')
    icdc.assert_no_failures()
