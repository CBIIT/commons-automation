"""TC11_C3DC_Verify_Analyzer_Venn_Region_Selection — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC11_C3DC_Verify_Analyzer_Venn_Region_Selection(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC11_C3DC_Verify_Analyzer_Venn_Region_Selection'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC11_C3DC_Verify_Analyzer_Venn_Region_Selection', '')
    c3dc.verify_analyzer_regions()
    c3dc.assert_no_failures()
