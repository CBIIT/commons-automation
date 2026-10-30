"""Migrated from Katalon INS_TestCases/SpecialTopic/TC05_INS_SpecialTopic-PediatricAYA/Script1729885994390.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC05_INS_SpecialTopic_PediatricAYA(ins):
    ins.load_query_file("TC05_INS_SpecialTopic-PediatricAYA.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("SpecialTopic/SpecialTopic", "PediatricAYA")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
