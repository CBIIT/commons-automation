"""Migrated from Katalon INS_TestCases/CancerType/TC05_INS_CancerType-CervicalCancer/Script1727713356285.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC05_INS_CancerType_CervicalCancer(ins):
    ins.load_query_file("TC05_INS_CancerType-CervicalCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "CervicalCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
