"""Migrated from Katalon INS_TestCases/CancerType/TC12_INS_CancerType-LungCancer/Script1727716176299.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC12_INS_CancerType_LungCancer(ins):
    ins.load_query_file("TC12_INS_CancerType-LungCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "LungCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
