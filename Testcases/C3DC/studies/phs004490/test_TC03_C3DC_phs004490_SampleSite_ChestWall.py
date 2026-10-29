"""Explore phs004490 with Sample Anatomic Site chest wall."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC03_C3DC_phs004490_SampleSite_ChestWall(c3dc):
    c3dc.load_query_file("TC03_C3DC_phs004490_SampleSite-ChestWall.xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs004490")
    c3dc.select_filter("Samples/SampleAnatomicSite", "ChestWall")
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
