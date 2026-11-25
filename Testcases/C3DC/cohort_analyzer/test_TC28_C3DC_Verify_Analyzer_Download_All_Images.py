"""TC28_C3DC_Verify_Analyzer_Download_All_Images — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC28_C3DC_Verify_Analyzer_Download_All_Images(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC28_C3DC_Verify_Analyzer_Download_All_Images'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.verify_analyzer_image_downloads()
    c3dc.assert_no_failures()
