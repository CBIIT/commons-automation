"""Migrated from Katalon INS_TestCases/SpecialTopic/TC02_INS_SpecialTopic-HealthDisparities/Script1729886025881.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC02_INS_SpecialTopic_HealthDisparities(ins):
    ins.load_query_file("TC02_INS_SpecialTopic-HealthDisparities.xlsx")
    ins.open_programs()
    ins.select_filter("SpecialTopic/SpecialTopic", "HealthDisparities")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.assert_no_failures()
