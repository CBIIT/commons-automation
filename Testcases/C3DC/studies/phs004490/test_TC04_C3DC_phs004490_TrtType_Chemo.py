"""Explore phs004490 with Treatment Type Chemotherapy."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC04_C3DC_phs004490_TrtType_Chemo(c3dc):
    c3dc.load_query_file("TC04_C3DC_phs004490_TrtType-Chemo.xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs004490")
    c3dc.select_filter("Treatment/TreatmentType", "Chemotherapy")
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
