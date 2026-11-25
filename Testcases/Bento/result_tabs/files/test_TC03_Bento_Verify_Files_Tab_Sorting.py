"""TC03_Bento_Verify_Files_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC03_Bento_Verify_Files_Tab_Sorting(bento):
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/Diagnosis', 'Adenocarcinoma')
    bento.verify_result_tab_sorting('Files', 'TC03_Bento_Verify_Files_Tab_Sorting')
    bento.assert_no_failures()
