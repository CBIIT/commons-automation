"""Explore phs004232 with Diagnosis Diagnosis Basis Clinical; compare stat bar and tabs to Memgraph."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.datarelease
def test_TC05_C3DC_phs004232_DiagnBasis_Clinical(c3dc):
    c3dc.load_query_file("TC05_C3DC_phs004232_DiagnBasis-Clinical.xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs004232")
    c3dc.select_filter("Diagnosis/DiagnosisBasis", "Clinical")
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
