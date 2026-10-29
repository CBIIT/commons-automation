"""Migrated from Katalon INS_TestCases/CancerType/TC21_INS_CancerType-ProstateCancer/Script1730854158563.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC21_INS_CancerType_ProstateCancer(ins):
    ins.load_query_file("TC21_INS_CancerType-ProstateCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "ProstateCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
