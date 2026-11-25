"""TC06_CTDC_Verify_Cart_ManifestCsv_Download — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC06_CTDC_Verify_Cart_ManifestCsv_Download(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC06_CTDC_Verify_Cart_ManifestCsv_Download')
    ctdc.file_cart.download_manifest('TC06_CTDC_Verify_Cart_ManifestCsv_Download')
    ctdc.file_cart.verify_manifest()
    ctdc.assert_no_failures()
