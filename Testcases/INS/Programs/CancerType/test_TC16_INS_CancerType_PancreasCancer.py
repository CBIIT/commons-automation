"""TC16_INS_CancerType-PancreasCancer — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC16_INS_CancerType_PancreasCancer(ins):
    ins.load_query_file('TC16_INS_CancerType-PancreasCancer.xlsx')
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter('CancerType/CancerType', 'PancreasCancer')
    ins.read_statbar()
    ins.verify_tab('Programs')
    ins.verify_tab('Projects')
    ins.verify_tab('Grants')
    ins.verify_tab('Publications')
    ins.assert_no_failures()
