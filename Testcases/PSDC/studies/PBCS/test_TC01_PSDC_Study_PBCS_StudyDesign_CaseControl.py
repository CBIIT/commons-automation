"""TC01_PSDC_Study_PBCS_StudyDesign-CaseControl — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_PSDC_Study_PBCS_StudyDesign_CaseControl(psdc):
    psdc.load_query_file('TC01_PSDC_Study_PBCS_StudyDesign-CaseControl.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Studies/StudyDesign', 'Case-Control Study')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
