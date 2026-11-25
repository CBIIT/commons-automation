"""TC01_INS_Verify_Projects_Tab_CSV_Download — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC01_INS_Verify_Projects_Tab_CSV_Download(ins):
    ins.load_query_file('INS_ResultTabDownloads.xlsx')
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter('CancerType/CancerType', 'EsophagealCancer')
    ins.result_tabs.download('Projects', 'CSV', 'TC01_INS_Verify_Projects_Tab_CSV_Download')
    ins.result_tabs.verify_download('Projects', 'CSV')
    ins.assert_no_failures()
