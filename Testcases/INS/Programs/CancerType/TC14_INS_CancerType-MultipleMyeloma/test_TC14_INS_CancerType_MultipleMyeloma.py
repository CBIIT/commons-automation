"""Migrated from Katalon INS_TestCases/CancerType/TC14_INS_CancerType-MultipleMyeloma/Script1727716591170.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC14_INS_CancerType_MultipleMyeloma(ins):
    ins.load_query_file("TC14_INS_CancerType-MultipleMyeloma.xlsx")
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "MultipleMyeloma")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
