"""Explore phs004232 with Samples Sample Tumor Status Not Reported; compare stat bar and tabs to Memgraph."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.datarelease
def test_TC04_C3DC_phs004232_SampleTumorStatus_NotReported(c3dc):
    c3dc.load_query_file("TC04_C3DC_phs004232_SampleTumorStatus-NotReported.xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs004232")
    c3dc.select_filter("Samples/SampleTumorStatus", "NotReported")
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
