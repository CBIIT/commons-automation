"""Migrated from Katalon INS_TestCases/CancerType/TC13_INS_CancerType-Lymphoma/Script1727716380990.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC13_INS_CancerType_Lymphoma(ins):
    ins.load_query_file("TC13_INS_CancerType-Lymphoma.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("CancerType/CancerType", "Lymphoma")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
