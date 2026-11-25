"""TC11_ICDC_Verify_Cart_EmptyState — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC11_ICDC_Verify_Cart_EmptyState(icdc):
    icdc.accept_banner()
    icdc.file_cart.open()
    icdc.file_cart.verify_empty('TC11_ICDC_Verify_Cart_EmptyState')
    icdc.assert_no_failures()
