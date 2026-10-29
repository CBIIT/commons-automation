"""Open Explore, select study phs002827 with Samples Tumor Spatial Extent Metastatic, then compare stat bar and tabs to Memgraph."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC06_C3DC_phs002827_TumorSpatialExtent_Metastatic(c3dc):
    c3dc.load_query_file("TC06_C3DC_phs002827_TumorSpatialExtent-Metastatic.xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs002827")
    c3dc.select_filter("Samples/TumorSpatialExtent", "Metastatic")
    c3dc.read_statbar()
    c3dc.verify_tab("Participants")
    c3dc.verify_tab("Studies")
    c3dc.verify_tab("Diagnosis")
    c3dc.verify_tab("Genetic Analysis")
    c3dc.verify_tab("Treatments")
    c3dc.verify_tab("Treatment Responses")
    c3dc.verify_tab("Survival")
    c3dc.verify_tab("Samples")
    c3dc.assert_no_failures()
