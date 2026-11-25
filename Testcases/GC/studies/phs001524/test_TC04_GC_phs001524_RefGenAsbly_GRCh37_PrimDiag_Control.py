"""TC04_GC_phs001524_RefGenAsbly-GRCh37_PrimDiag-Control — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC04_GC_phs001524_RefGenAsbly_GRCh37_PrimDiag_Control(gc):
    gc.load_query_file('TC04_GC_phs001524_RefGenAsbly-GRCh37_PrimDiag-Control.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001524')
    gc.select_filter('GenomicFacet/ReferenceGenomeAssembly', 'GRCh37')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'Control')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
