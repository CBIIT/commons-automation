"""C3DC About, Release Notes and User Guide static-content checks."""


def open_about_page(app):
    """Open the about page in the configured environment."""
    app.goto('about')


def verify_about_page_content(app):
    """Compare text and links with the AboutPage sheet of C3DC_StaticData.xlsx."""
    app.verify_static_data('AboutPage')


# ---------------------------------------------------------------------------
# Release Notes: compare viewer metadata and verify the embedded PDF response.
# ---------------------------------------------------------------------------

def open_release_notes(app):
    app.goto('release-notes-pdf')


def verify_release_notes_content(app):
    """Check workbook expectations and the document served by the visible viewer."""
    from urllib.parse import urljoin
    app.verify_static_data('ReleaseNotesPage')
    viewer = app.ui.visible(app.repo.xpath('Static/ReleaseNotesPage/ViewerTitle'))
    source = viewer.get_attribute('src')
    assert source, 'Release Notes viewer has no document source'
    response = app.page.request.get(urljoin(app.page.url, source))
    assert response.ok, f'Release Notes PDF request failed: HTTP {response.status}'
    content = response.body()
    assert 'application/pdf' in response.headers.get('content-type', '').lower(), 'Release Notes source did not return PDF content'
    assert content.startswith(b'%PDF-') and len(content) > 5, 'Release Notes PDF is empty or invalid'
    app.results.append({'check': 'Release Notes PDF', 'status': 'PASSED', 'detail': f'PDF response verified ({len(content)} bytes)'})


# ---------------------------------------------------------------------------
# User Guide: About menu opens the full guide PDF in a separate browser tab.
# ---------------------------------------------------------------------------

def open_user_guide(app):
    """Follow About > User Guide and retain the actual PDF URL for verification."""
    from urllib.parse import urljoin
    app.click('Static/UserGuidePage/AboutMenu')
    link = app.ui.visible(app.repo.xpath('Static/UserGuidePage/GuideLink'))
    source = urljoin(app.page.url, link.get_attribute('href'))
    # Headless Chromium may expose a native PDF tab with no normal page URL.
    # Observe the actual request triggered by the click instead of waiting for HTML.
    with app.page.context.expect_event('request', predicate=lambda request: request.url == source, timeout=app.ui.timeout_ms) as requested:
        with app.page.expect_popup(timeout=app.ui.timeout_ms) as opened:
            link.click()
    app._user_guide_pdf_url = requested.value.url
    opened.value.close()


def verify_user_guide_content(app):
    """Verify the full PDF's title and section text from the UserGuidePage sheet."""
    from io import BytesIO
    from pathlib import Path
    import openpyxl
    from pypdf import PdfReader
    from Commons.settings import input_dir

    response = app.page.request.get(app._user_guide_pdf_url)
    assert response.ok, f'User Guide PDF request failed: HTTP {response.status}'
    content = response.body()
    assert 'application/pdf' in response.headers.get('content-type', '').lower(), 'User Guide did not return PDF content'
    assert content.startswith(b'%PDF-'), 'User Guide response is not a PDF'
    reader = PdfReader(BytesIO(content))
    assert reader.pages, 'User Guide PDF has no pages'
    text = ' '.join(' '.join(page.extract_text() or '' for page in reader.pages).split()).casefold()
    target = app.output_dir / 'user_guide.pdf'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    workbook = openpyxl.load_workbook(Path(input_dir(app.NAME)) / app.STATIC_DATA_EXCEL, data_only=True, read_only=True)
    try:
        rows = list(workbook['UserGuidePage'].iter_rows(min_row=2, values_only=True))
    finally:
        workbook.close()
    assert rows, 'UserGuidePage must contain expected PDF text'
    for row in rows:
        if not row[0]:
            continue
        expected = ' '.join(str(row[1]).split()).casefold()
        if not expected or expected not in text:
            app._fail(f'User Guide PDF {row[0]}: expected text not found: {row[1]}')
        else:
            app.results.append({'check': f'User Guide PDF {row[0]}', 'status': 'PASSED', 'detail': str(row[1])})


# ---------------------------------------------------------------------------
# Explore help panels: separate workbook sheets share the same modal workflow.
# ---------------------------------------------------------------------------

def verify_explore_help_content(app, sheet_name):
    """Open, compare and close a help panel using its repository and input sheet."""
    from playwright.sync_api import expect
    prefix = f'Static/{sheet_name}/'
    app.click(prefix + 'Open')
    content = app.page.locator(app.repo.xpath(prefix + 'Content'))
    expect(content).to_be_visible(timeout=app.ui.timeout_ms)
    app.verify_static_data(sheet_name)
    app.click(prefix + 'Close')
    expect(content).not_to_be_visible(timeout=app.ui.timeout_ms)
