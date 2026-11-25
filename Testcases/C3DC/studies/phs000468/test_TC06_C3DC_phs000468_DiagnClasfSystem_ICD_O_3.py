"""TC06_C3DC_phs000468_DiagnClasfSystem-ICD-O-3 — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC06_C3DC_phs000468_DiagnClasfSystem_ICD_O_3(c3dc):
    c3dc.load_query_file('TC06_C3DC_phs000468_DiagnClasfSystem-ICD-O-3.xlsx')
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs000468')
    c3dc.select_filter('Diagnosis/DiagsClasifctnSystem', 'ICD-O-3.2')
    c3dc.read_statbar()
    c3dc.verify_tab('Participants')
    c3dc.verify_tab('Studies')
    c3dc.sort_result_tab('GeneticAnalysis', 'ResultTabs/SortByGeneticAnalysisID-Colm')
    c3dc.verify_tab('Genetic Analysis')
    c3dc.verify_tab('Samples')
    c3dc.open_explore_files()
    c3dc.verify_tab('Files')
    c3dc.verify_tab('Imaging Data')
    c3dc.assert_no_failures()
