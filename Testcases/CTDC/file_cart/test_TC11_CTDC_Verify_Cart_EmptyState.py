"""TC11_CTDC_Verify_Cart_EmptyState — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC11_CTDC_Verify_Cart_EmptyState(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open()
    ctdc.file_cart.verify_empty('TC11_CTDC_Verify_Cart_EmptyState')
    ctdc.assert_no_failures()
