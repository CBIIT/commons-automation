"""Migrated from Katalon INS_TestCases/CancerType/TC18_INS_CancerType-HeadandNeckCancer/Script1730853773987.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC18_INS_CancerType_HeadandNeckCancer(ins):
    ins.load_query_file("TC18_INS_CancerType-HeadandNeckCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "HeadandNeckCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
