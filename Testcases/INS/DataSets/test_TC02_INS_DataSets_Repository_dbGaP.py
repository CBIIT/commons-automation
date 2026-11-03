"""Migrated from Katalon INS_TestCases/DataSets/TC02_INS_DataSets_Repository-dbGaP/Script1747922784610.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC02_INS_DataSets_Repository_dbGaP(ins):
    ins.load_query_file("TC02_INS_DataSets_Repository-dbGaP.xlsx")
    ins.accept_banner()
    ins.open_datasets()
    ins.select_filter("DataSets/Repository", "dbGaP")
    ins.verify_datasets()
    ins.assert_no_failures()
