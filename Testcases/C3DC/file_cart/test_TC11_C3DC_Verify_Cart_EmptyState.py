"""TC11_C3DC_Verify_Cart_EmptyState — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC11_C3DC_Verify_Cart_EmptyState(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open()
    c3dc.file_cart.verify_empty('TC11_C3DC_Verify_Cart_EmptyState')
    c3dc.assert_no_failures()
