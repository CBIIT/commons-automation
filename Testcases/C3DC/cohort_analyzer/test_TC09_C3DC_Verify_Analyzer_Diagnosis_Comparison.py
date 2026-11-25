"""TC09_C3DC_Verify_Analyzer_Diagnosis_Comparison — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC09_C3DC_Verify_Analyzer_Diagnosis_Comparison(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC09_C3DC_Verify_Analyzer_Diagnosis_Comparison'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.remember_analyzer_cohorts('TC09_C3DC_Verify_Analyzer_Diagnosis_Comparison', 'clinical')
    c3dc.verify_analyzer_comparison('Diagnosis')
    c3dc.assert_no_failures()
