"""TC05_GC_phs001437_RefGenAsbly-GRCh38_PrimDiag-CPNET — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC05_GC_phs001437_RefGenAsbly_GRCh38_PrimDiag_CPNET(gc):
    gc.load_query_file('TC05_GC_phs001437_RefGenAsbly-GRCh38_PrimDiag-CPNET.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs001437')
    gc.select_filter('GenomicFacet/ReferenceGenomeAssembly', 'GRCh38')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'CPNET')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
