"""TC18_C3DC_Verify_Analyzer_Chart_Counts_Percentages — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC18_C3DC_Verify_Analyzer_Chart_Counts_Percentages(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC18_C3DC_Verify_Analyzer_Chart_Counts_Percentages'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC18_C3DC_Verify_Analyzer_Chart_Counts_Percentages', 'clinical')
    c3dc.verify_analyzer_chart_values()
    c3dc.assert_no_failures()
