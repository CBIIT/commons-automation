"""Migrated from Katalon INS_TestCases/SpecialTopic/TC03_INS_SpecialTopic-HIV_AIDS/Script1729886015994.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC03_INS_SpecialTopic_HIV_AIDS(ins):
    ins.load_query_file("TC03_INS_SpecialTopic-HIV_AIDS.xlsx")
    ins.accept_banner()
    ins.open_programs()
    ins.select_filter("SpecialTopic/SpecialTopic", "HIVAIDS")
    ins.read_statbar()
    ins.verify_tab("Programs")
    ins.verify_tab("Projects")
    ins.verify_tab("Grants")
    ins.verify_tab("Publications")
    ins.assert_no_failures()
