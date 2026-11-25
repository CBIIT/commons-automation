"""TC19_C3DC_Verify_Analyzer_Chart_Types — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC19_C3DC_Verify_Analyzer_Chart_Types(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC19_C3DC_Verify_Analyzer_Chart_Types'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.verify_analyzer_chart_types()
    c3dc.assert_no_failures()
