"""Migrated from Katalon INS_TestCases/CancerType/TC02_INS_CancerType-BrainCancer/Script1727195684624.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC02_INS_CancerType_BrainCancer(ins):
    ins.load_query_file("TC02_INS_CancerType-BrainCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "BrainCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
