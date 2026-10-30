"""Migrated from Katalon INS_TestCases/CancerType/TC22_INS_CancerType-Sarcoma/Script1730854176018.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC22_INS_CancerType_Sarcoma(ins):
    ins.load_query_file("TC22_INS_CancerType-Sarcoma.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "Sarcoma")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
