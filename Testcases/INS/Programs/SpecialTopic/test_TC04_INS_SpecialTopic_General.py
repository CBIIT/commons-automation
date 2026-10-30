"""Migrated from Katalon INS_TestCases/SpecialTopic/TC04_INS_SpecialTopic-General/Script1729886361618.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC04_INS_SpecialTopic_General(ins):
    ins.load_query_file("TC04_INS_SpecialTopic-General.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("SpecialTopic/SpecialTopic", "General")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
