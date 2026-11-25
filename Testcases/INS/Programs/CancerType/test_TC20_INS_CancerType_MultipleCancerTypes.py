"""TC20_INS_CancerType-MultipleCancerTypes — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC20_INS_CancerType_MultipleCancerTypes(ins):
    ins.load_query_file('TC20_INS_CancerType-MultipleCancerTypes.xlsx')
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter('CancerType/CancerType', 'MultipleCancerTypes')
    ins.read_statbar()
    ins.verify_tab('Programs')
    ins.verify_tab('Projects')
    ins.verify_tab('Grants')
    ins.verify_tab('Publications')
    ins.assert_no_failures()
