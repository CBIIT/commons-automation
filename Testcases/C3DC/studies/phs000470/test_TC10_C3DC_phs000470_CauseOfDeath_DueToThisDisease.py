"""TC10_C3DC_phs000470_CauseOfDeath-DueToThisDisease — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC10_C3DC_phs000470_CauseOfDeath_DueToThisDisease(c3dc):
    c3dc.load_query_file('TC10_C3DC_phs000470_CauseOfDeath-DueToThisDisease.xlsx')
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter('Study/dbGaP_Accession', 'phs000470')
    c3dc.select_filter('Survival/CauseOfDeath', 'DueToThisDisease')
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
