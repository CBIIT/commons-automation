"""Migrated from Katalon INS_TestCases/CancerType/TC17_INS_CancerType-ThyroidCancer/Script1727717117020.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC17_INS_CancerType_ThyroidCancer(ins):
    ins.load_query_file("TC17_INS_CancerType-ThyroidCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "ThyroidCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
