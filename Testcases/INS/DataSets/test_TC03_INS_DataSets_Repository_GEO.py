"""TC03_INS_DataSets_Repository-GEO — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
def test_TC03_INS_DataSets_Repository_GEO(ins):
    ins.load_query_file('TC03_INS_DataSets_Repository-GEO.xlsx')
    ins.accept_banner()
    ins.open_datasets()
    ins.select_filter('DataSets/Repository', 'GEO')
    ins.verify_datasets()
    ins.assert_no_failures()
