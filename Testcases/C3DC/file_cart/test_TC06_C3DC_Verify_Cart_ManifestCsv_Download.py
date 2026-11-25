"""TC06_C3DC_Verify_Cart_ManifestCsv_Download — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC06_C3DC_Verify_Cart_ManifestCsv_Download(c3dc):
    c3dc.accept_banner()
    c3dc.file_cart.open_explore_files()
    c3dc.file_cart.select_files(3)
    c3dc.file_cart.add_selected()
    c3dc.file_cart.open()
    c3dc.file_cart.verify('TC06_C3DC_Verify_Cart_ManifestCsv_Download')
    c3dc.file_cart.download_manifest('TC06_C3DC_Verify_Cart_ManifestCsv_Download')
    c3dc.file_cart.verify_manifest()
    c3dc.assert_no_failures()
