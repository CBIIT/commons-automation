"""Migrated from Katalon INS_TestCases/CancerType/TC15_INS_CancerType-OvarianCancer/Script1727716752875.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC15_INS_CancerType_OvarianCancer(ins):
    ins.load_query_file("TC15_INS_CancerType-OvarianCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "OvarianCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
