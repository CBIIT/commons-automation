"""TC03_Bento_Verify_Cases_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC03_Bento_Verify_Cases_Tab_Sorting(bento):
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/Diagnosis', 'Adenocarcinoma')
    bento.verify_result_tab_sorting('Cases', 'TC03_Bento_Verify_Cases_Tab_Sorting')
    bento.assert_no_failures()
