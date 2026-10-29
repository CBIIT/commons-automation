"""Migrated from Katalon INS_TestCases/CancerType/TC04_INS_CancerType-GynecologicCancer/Script1730759763513.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC04_INS_CancerType_GynecologicCancer(ins):
    ins.load_query_file("TC04_INS_CancerType-GynecologicCancer.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "GynecologicCancer")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
