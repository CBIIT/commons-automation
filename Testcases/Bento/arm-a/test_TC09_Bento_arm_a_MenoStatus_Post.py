"""TC09_Bento_arm-a_MenoStatus-Post — Python regression case."""

import pytest


@pytest.mark.bento
@pytest.mark.regression
def test_TC09_Bento_arm_a_MenoStatus_Post(bento):
    bento.load_query_file('TC09_Bento_arm-a_MenoStatus-Post.xlsx')
    bento.accept_banner()
    bento.open_cases()
    bento.select_filter('Filter/Arm', 'A')
    bento.select_filter('Filter/MenopauseStatus', 'Post')
    bento.read_statbar()
    bento.verify_tab('Cases')
    bento.verify_tab('Samples')
    bento.verify_tab('Files')
    bento.assert_no_failures()
