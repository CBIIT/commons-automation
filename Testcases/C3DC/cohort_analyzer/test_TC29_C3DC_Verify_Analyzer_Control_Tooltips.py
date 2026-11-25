"""TC29_C3DC_Verify_Analyzer_Control_Tooltips — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC29_C3DC_Verify_Analyzer_Control_Tooltips(c3dc):
    c3dc.accept_banner()
    c3dc._analyzer_output = c3dc.output_dir / 'TC29_C3DC_Verify_Analyzer_Control_Tooltips'
    c3dc.open_cohort_analyzer()
    c3dc.add_example_cohorts()
    c3dc.verify_analyzer_tooltip('ExpandVenn', 'Expand chart')
    c3dc.verify_analyzer_tooltip('DownloadVenn', 'Download')
    c3dc.verify_analyzer_tooltip('VennHelp', 'The venn diagram is a stylized representation of the selected cohorts and their shared Participant IDs, and are not proportionally accurate,')
    c3dc.verify_analyzer_tooltip('MatchingHelp', 'All Venn diagram selected areas will be cleared when changing buttons')
    c3dc.verify_analyzer_tooltip('DragHelp', 'Drag to reorder cards')
    c3dc.verify_analyzer_tooltip('ResizeHelp', 'Drag to resize chart')
    c3dc.assert_no_failures()
