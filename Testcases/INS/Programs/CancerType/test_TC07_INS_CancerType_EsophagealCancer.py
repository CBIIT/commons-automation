"""Migrated from Katalon INS_TestCases/CancerType/TC07_INS_CancerType-EsophagealCancer/Script1727714609586.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC07_INS_CancerType_EsophagealCancer(ins):
    ins.load_query_file("TC07_INS_CancerType-EsophagealCancer.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "EsophagealCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
