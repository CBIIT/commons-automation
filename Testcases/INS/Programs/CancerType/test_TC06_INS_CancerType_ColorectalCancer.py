"""Migrated from Katalon INS_TestCases/CancerType/TC06_INS_CancerType-ColorectalCancer/Script1727714219993.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC06_INS_CancerType_ColorectalCancer(ins):
    ins.load_query_file("TC06_INS_CancerType-ColorectalCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "ColorectalCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
