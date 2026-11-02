"""Migrated from Katalon INS_TestCases/DataSets/TC01_INS_DataSets_Repository-CEDCD/Script1747914444747.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_INS_DataSets_Repository_CEDCD(ins):
    ins.load_query_file("TC01_INS_DataSets_Repository-CEDCD.xlsx")
    ins.accept_banner()
    ins.open_datasets()
    ins.select_filter("DataSets/Repository", "CEDCD")
    ins.verify_datasets()
    ins.assert_no_failures()
