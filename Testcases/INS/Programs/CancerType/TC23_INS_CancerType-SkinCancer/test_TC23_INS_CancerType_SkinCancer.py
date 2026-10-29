"""Migrated from Katalon INS_TestCases/CancerType/TC23_INS_CancerType-SkinCancer/Script1730854236673.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC23_INS_CancerType_SkinCancer(ins):
    ins.load_query_file("TC23_INS_CancerType-SkinCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "SkinCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
