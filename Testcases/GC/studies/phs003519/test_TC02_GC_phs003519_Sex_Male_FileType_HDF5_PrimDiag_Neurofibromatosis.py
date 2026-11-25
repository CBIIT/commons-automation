"""TC02_GC_phs003519_Sex-Male_FileType-HDF5_PrimDiag_Neurofibromatosis — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC02_GC_phs003519_Sex_Male_FileType_HDF5_PrimDiag_Neurofibromatosis(gc):
    gc.load_query_file('TC02_GC_phs003519_Sex-Male_FileType-HDF5_PrimDiag_Neurofibromatosis.xlsx')
    gc.accept_banner()
    gc.open_data()
    gc.select_filter('StudyFacet/PHS_Accession', 'phs003519')
    gc.select_filter('DemographicsFacet/Sex', 'Male')
    gc.select_filter('DiagnosisFacet/PrimaryDiagnosis', 'NeurofibromatosisNOS')
    gc.select_filter('FilesFacet/FileType', 'hdf5')
    gc.read_statbar()
    gc.verify_tab('Participants')
    gc.verify_tab('Samples')
    gc.verify_tab('Files')
    gc.assert_no_failures()
