"""Migrated from Katalon INS_TestCases/SpecialTopic/TC01_INS_SpecialTopic-CancerMoonshot/Script1729886033833.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC01_INS_SpecialTopic_CancerMoonshot(ins):
    ins.load_query_file("TC01_INS_SpecialTopic-CancerMoonshot.xlsx")
    ins.open_programs()
    ins.select_filter("SpecialTopic/SpecialTopic", "Moonshot")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
