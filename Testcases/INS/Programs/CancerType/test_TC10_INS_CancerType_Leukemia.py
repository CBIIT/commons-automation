"""TC10_INS_CancerType-Leukemia — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC10_INS_CancerType_Leukemia(ins):
    ins.load_query_file('TC10_INS_CancerType-Leukemia.xlsx')
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter('CancerType/CancerType', 'Leukemia')
    ins.read_statbar()
    ins.verify_tab('Programs')
    ins.verify_tab('Projects')
    ins.verify_tab('Grants')
    ins.verify_tab('Publications')
    ins.assert_no_failures()
