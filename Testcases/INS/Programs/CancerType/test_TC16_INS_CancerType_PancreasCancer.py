"""Migrated from Katalon INS_TestCases/CancerType/TC16_INS_CancerType-PancreasCancer/Script1727716935842.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC16_INS_CancerType_PancreasCancer(ins):
    ins.load_query_file("TC16_INS_CancerType-PancreasCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "PancreasCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
