"""TC01_GC_phs001713_Gender-Male_ExperimentalStrategy-TargetedCapture — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs001713_Gender_Male_ExperimentalStrategy_TargetedCapture(gc):
    gc.load_query_file('TC01_GC_phs001713_Gender-Male_ExperimentalStrategy-TargetedCapture.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001713')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'TargetedCapture')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
