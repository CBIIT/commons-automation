"""TC12_Bento_arm-b_TissueComp-SolidTissue — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC12_Bento_arm_b_TissueComp_SolidTissue(bento):
    bento.load_query_file('TC12_Bento_arm-b_TissueComp-SolidTissue.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'B')
    bento.select_filter('Filter/TissueComposition', 'SolidTissue')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
