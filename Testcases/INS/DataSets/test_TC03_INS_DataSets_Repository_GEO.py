"""Migrated from Katalon INS_TestCases/DataSets/TC03_INS_DataSets_Repository-GEO/Script1747930787247.groovy."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
@pytest.mark.skip(reason='INS Datasets TSV compare not migrated yet')
def test_TC03_INS_DataSets_Repository_GEO(ins):
    ins.load_query_file("TC03_INS_DataSets_Repository-GEO.xlsx")
    ins.accept_banner()
    ins.open_datasets()
    pytest.skip('INS Datasets TSV compare not migrated yet')
