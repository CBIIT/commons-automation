"""TC01_ICDC_Verify_Case_Files_Tab_CSV_Download — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC01_ICDC_Verify_Case_Files_Tab_CSV_Download(icdc):
    icdc.load_query_file('ICDC_ResultTabDownloads.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_filter('Cases/Study', 'Canine_Filter_Study-COTC021')
    icdc.select_filter('Cases/Breed', 'BernMtnDog')
    icdc.result_tabs.download('Case Files', 'CSV', 'TC01_ICDC_Verify_Case_Files_Tab_CSV_Download')
    icdc.result_tabs.verify_download('Case Files', 'CSV')
    icdc.assert_no_failures()
