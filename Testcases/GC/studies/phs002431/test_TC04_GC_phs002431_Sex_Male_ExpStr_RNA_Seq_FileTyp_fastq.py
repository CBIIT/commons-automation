"""TC04_GC_phs002431_Sex_Male_ExpStr-RNA-Seq_FileTyp-fastq — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs002431_Sex_Male_ExpStr_RNA_Seq_FileTyp_fastq(gc):
    gc.load_query_file('TC04_GC_phs002431_Sex_Male_ExpStr-RNA-Seq_FileTyp-fastq.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs002431')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('StudyFacet/ExperimentalStrategy', 'RNASeq')
    gc.select_filter('FilesFacet/FileType', 'fastq')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
