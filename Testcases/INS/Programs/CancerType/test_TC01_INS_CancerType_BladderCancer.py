"""Migrated from Katalon INS_TestCases/CancerType/TC01_INS_CancerType-BladderCancer/Script1727191150711.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC01_INS_CancerType_BladderCancer(ins):
    ins.load_query_file("TC01_INS_CancerType-BladderCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "BladderCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
