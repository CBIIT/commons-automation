"""TC03_INS_Verify_Projects_Tab_Sorting — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC03_INS_Verify_Projects_Tab_Sorting(ins):
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter('CancerType/CancerType', 'EsophagealCancer')
    ins.verify_result_tab_sorting('Projects', 'TC03_INS_Verify_Projects_Tab_Sorting')
    ins.assert_no_failures()
