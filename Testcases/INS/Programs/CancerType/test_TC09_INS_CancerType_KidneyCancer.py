"""Migrated from Katalon INS_TestCases/CancerType/TC09_INS_CancerType-KidneyCancer/Script1727715500145.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC09_INS_CancerType_KidneyCancer(ins):
    ins.load_query_file("TC09_INS_CancerType-KidneyCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "KidneyCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
