"""TC01_ICDC_OSA02_StudyType-TranscrGenomics — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC01_ICDC_OSA02_StudyType_TranscrGenomics(icdc):
    icdc.load_query_file('TC01_ICDC_OSA02_StudyType-TranscrGenomics.xlsx')
    icdc.accept_banner()
    icdc.open_cases()
    icdc.select_study('Canine_Filter_Study-OSA02')
    icdc.select_filter('Cases/StudyType', 'Canine_Filter_StudyType-TranscrpGenom')
    icdc.read_statbar()
    icdc.verify_tab('Cases')
    icdc.verify_tab('Samples')
    icdc.verify_tab('Case Files')
    icdc.verify_tab('Study Files')
    icdc.assert_no_failures()
