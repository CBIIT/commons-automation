"""Migrated from Katalon INS_TestCases/CancerType/TC03_INS_CancerType-BreastCancer/Script1727458074206.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC03_INS_CancerType_BreastCancer(ins):
    ins.load_query_file("TC03_INS_CancerType-BreastCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "BreastCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
