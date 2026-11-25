"""TC02_CTDC_Verify_Cart_AddAllFilteredFiles — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC02_CTDC_Verify_Cart_AddAllFilteredFiles(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_study_source()
    ctdc.file_cart.add_all_filtered(50)
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC02_CTDC_Verify_Cart_AddAllFilteredFiles')
    ctdc.assert_no_failures()
