"""TC05_C3DC_phs000468_Diagnosis-OsteosarNOS — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC05_C3DC_phs000468_Diagnosis_OsteosarNOS(c3dc):
    c3dc.load_query_file('TC05_C3DC_phs000468_Diagnosis-OsteosarNOS.xlsx')
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs000468')
    c3dc.select_filter('Diagnosis/Diagnosis', 'OsteosarNOS')
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
