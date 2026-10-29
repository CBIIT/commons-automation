"""Migrated from Katalon INS_TestCases/SpecialTopic/TC06_INS_SpecialTopic-SPORE/Script1729885985446.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC06_INS_SpecialTopic_SPORE(ins):
    ins.load_query_file("TC06_INS_SpecialTopic-SPORE.xlsx")
    ins.open_programs()
    ins.select_filter("SpecialTopic/SpecialTopic", "SPORE")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
