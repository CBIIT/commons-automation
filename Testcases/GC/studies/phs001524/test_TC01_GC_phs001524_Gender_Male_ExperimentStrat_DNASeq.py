"""TC01_GC_phs001524_Gender-Male_ExperimentStrat-DNASeq — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_phs001524_Gender_Male_ExperimentStrat_DNASeq(gc):
    gc.load_query_file('TC01_GC_phs001524_Gender-Male_ExperimentStrat-DNASeq.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001524')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'DNASeq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
