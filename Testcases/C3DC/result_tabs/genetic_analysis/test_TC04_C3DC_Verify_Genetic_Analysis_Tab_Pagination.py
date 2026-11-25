"""TC04_C3DC_Verify_Genetic_Analysis_Tab_Pagination — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC04_C3DC_Verify_Genetic_Analysis_Tab_Pagination(c3dc):
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    c3dc.verify_result_tab_pagination('GeneticAnalysis', page_sizes=[50, 100], report_name='TC04_C3DC_Verify_Genetic_Analysis_Tab_Pagination')
    c3dc.assert_no_failures()
