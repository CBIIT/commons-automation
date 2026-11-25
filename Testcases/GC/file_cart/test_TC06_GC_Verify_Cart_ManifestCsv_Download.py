"""TC06_GC_Verify_Cart_ManifestCsv_Download — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC06_GC_Verify_Cart_ManifestCsv_Download(gc):
    gc.accept_banner()
    gc.file_cart.open_explore_files()
    gc.file_cart.select_files(3)
    gc.file_cart.add_selected()
    gc.file_cart.open()
    gc.file_cart.verify('TC06_GC_Verify_Cart_ManifestCsv_Download')
    gc.file_cart.download_manifest('TC06_GC_Verify_Cart_ManifestCsv_Download')
    gc.file_cart.verify_manifest()
    gc.assert_no_failures()
