"""Migrated from Katalon INS_TestCases/CancerType/TC08_INS_CancerType-GastricCancer/Script1727715176568.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC08_INS_CancerType_GastricCancer(ins):
    ins.load_query_file("TC08_INS_CancerType-GastricCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "GastricCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
