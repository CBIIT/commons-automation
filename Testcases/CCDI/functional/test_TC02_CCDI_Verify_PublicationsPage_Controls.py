"""TC02_CCDI_Verify_PublicationsPage_Controls — Python regression case."""

import pytest


@pytest.mark.ccdi
def test_TC02_CCDI_Verify_PublicationsPage_Controls(ccdi):
    ccdi.accept_banner()
    ccdi.click('Navbar/About-Btn')
    ccdi.click('Navbar/About-Publications-Btn')
    ccdi.load_publications_source('publications/CCDISupportedPublications.xlsx')
    ccdi.verify_publications_category('All')
    ccdi.verify_publications_category('Primary')
    ccdi.verify_publications_category('Secondary')
    ccdi.verify_publications_category('Abstracts')
    ccdi.verify_publications_partition()
    ccdi.select_publication_category('All')
    ccdi.search_publications('OpenPBTA')
    ccdi.verify_publications_search('OpenPBTA', 'Ecosystem_05312023')
    ccdi.clear_publications_search()
    ccdi.submit_publications_search()
    ccdi.verify_publications_reset()
    ccdi.search_publications('openpbta')
    ccdi.verify_publications_search('openpbta', 'Ecosystem_05312023')
    ccdi.clear_publications_search()
    ccdi.submit_publications_search()
    ccdi.verify_publications_reset()
    ccdi.search_publications('zz_ccdi_no_publication_7d9f2b')
    ccdi.verify_empty_publications_search()
    ccdi.clear_publications_search()
    ccdi.submit_publications_search()
    ccdi.verify_publications_reset()
    ccdi.write_publication_results()
    ccdi.assert_no_failures()
