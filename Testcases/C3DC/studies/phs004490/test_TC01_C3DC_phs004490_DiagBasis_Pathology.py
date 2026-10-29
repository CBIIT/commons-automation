"""Explore phs004490 with Diagnosis Basis Pathology."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_phs004490_DiagBasis_Pathology(c3dc):
    c3dc.load_query_file("TC01_C3DC_phs004490_DiagBasis-Pathology.xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs004490")
    c3dc.select_filter("Diagnosis/DiagnosisBasis", "Pathology")
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
