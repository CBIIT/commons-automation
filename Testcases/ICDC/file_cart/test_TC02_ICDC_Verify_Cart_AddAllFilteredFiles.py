"""TC02_ICDC_Verify_Cart_AddAllFilteredFiles — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC02_ICDC_Verify_Cart_AddAllFilteredFiles(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_study_source()
    icdc.file_cart.add_all_filtered(50)
    icdc.file_cart.open()
    icdc.file_cart.verify('TC02_ICDC_Verify_Cart_AddAllFilteredFiles')
    icdc.assert_no_failures()
