"""Migrated from Katalon INS_TestCases/CancerType/TC19_INS_CancerType-Melanoma/Script1730853806284.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC19_INS_CancerType_Melanoma(ins):
    ins.load_query_file("TC19_INS_CancerType-Melanoma.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "Melanoma")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
