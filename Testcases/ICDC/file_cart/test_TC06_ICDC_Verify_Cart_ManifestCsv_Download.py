"""TC06_ICDC_Verify_Cart_ManifestCsv_Download — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC06_ICDC_Verify_Cart_ManifestCsv_Download(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC06_ICDC_Verify_Cart_ManifestCsv_Download')
    icdc.file_cart.download_manifest('TC06_ICDC_Verify_Cart_ManifestCsv_Download')
    icdc.file_cart.verify_manifest()
    icdc.assert_no_failures()
