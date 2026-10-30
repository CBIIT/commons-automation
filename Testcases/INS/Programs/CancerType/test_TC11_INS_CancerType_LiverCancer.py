"""Migrated from Katalon INS_TestCases/CancerType/TC11_INS_CancerType-LiverCancer/Script1727715977334.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC11_INS_CancerType_LiverCancer(ins):
    ins.load_query_file("TC11_INS_CancerType-LiverCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "LiverCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
