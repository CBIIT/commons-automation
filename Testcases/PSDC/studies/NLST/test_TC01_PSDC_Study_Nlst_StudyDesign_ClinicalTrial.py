"""TC01_PSDC_Study_Nlst_StudyDesign-ClinicalTrial — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_PSDC_Study_Nlst_StudyDesign_ClinicalTrial(psdc):
    psdc.load_query_file('TC01_PSDC_Study_Nlst_StudyDesign-ClinicalTrial.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('NLST')
    psdc.select_filter('Studies/StudyDesign', 'Clinical Trial')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
