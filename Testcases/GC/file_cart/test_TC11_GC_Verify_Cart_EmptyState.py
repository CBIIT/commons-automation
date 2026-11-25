"""TC11_GC_Verify_Cart_EmptyState — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC11_GC_Verify_Cart_EmptyState(gc):
    gc.accept_banner()
    gc.file_cart.open()
    gc.file_cart.verify_empty('TC11_GC_Verify_Cart_EmptyState')
    gc.assert_no_failures()
