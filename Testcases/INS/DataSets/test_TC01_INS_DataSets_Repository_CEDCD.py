"""Migrated from Katalon INS_TestCases/DataSets/TC01_INS_DataSets_Repository-CEDCD/Script1747914444747.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
@pytest.mark.skip(reason='INS Datasets TSV compare not migrated yet')
def test_TC01_INS_DataSets_Repository_CEDCD(ins):
    ins.load_query_file("TC01_INS_DataSets_Repository-CEDCD.xlsx")
    ins.accept_banner()
    ins.open_datasets()
    pytest.skip('INS Datasets TSV compare not migrated yet')
