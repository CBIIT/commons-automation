"""Independent C3DC static page workflows and shared workbook routing."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from Commons.apps.c3dc.app import C3DC
from Commons.apps.c3dc import home_page, static_pages
from Commons.excel_testcase.runner import run_testcase_excel

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('number,page,module', [(1, 'HomePage', 'home_page'), (2, 'AboutPage', 'about_page')])
def test_static_excel_verifies_only_its_own_page(number, page, module):
    app = Mock(spec=C3DC)
    path = ROOT / f'Testcases/C3DC/static/TC{number:02}_C3DC_Verify_{page}_Content.xlsx'
    run_testcase_excel(app, path)
    assert [call[0] for call in app.method_calls] == [
        'accept_banner', f'open_{module}', f'verify_{module}_content', 'assert_no_failures']


@pytest.mark.parametrize('module,sheet,route', [(home_page, 'HomePage', '/'), (static_pages, 'AboutPage', 'about')])
def test_page_helpers_reuse_static_engine_and_configured_navigation(module, sheet, route):
    app = Mock()
    getattr(module, 'open_home_page' if sheet == 'HomePage' else 'open_about_page')(app)
    getattr(module, 'verify_home_page_content' if sheet == 'HomePage' else 'verify_about_page_content')(app)
    app.goto.assert_called_once_with(route)
    app.verify_static_data.assert_called_once_with(sheet)


@pytest.mark.parametrize('number,page,open_action,verify_action', [
    (3, 'ReleaseNotes', 'open_release_notes', 'verify_release_notes_content'),
    (4, 'UserGuide', 'open_user_guide', 'verify_user_guide_content'),
])
def test_document_cases_dispatch_independently(number, page, open_action, verify_action):
    app = Mock(spec=C3DC)
    run_testcase_excel(app, ROOT / f'Testcases/C3DC/static/TC{number:02}_C3DC_Verify_{page}_Content.xlsx')
    assert [call[0] for call in app.method_calls] == ['accept_banner', open_action, verify_action, 'assert_no_failures']


@pytest.mark.parametrize('content_type,body,ok,passes', [
    ('application/pdf', b'%PDF-1.7 document', True, True),
    ('text/html', b'<html>not a PDF</html>', True, False),
    ('application/pdf', b'', True, False),
    ('application/pdf', b'%PDF-1.7 document', False, False),
])
def test_release_notes_reject_missing_or_invalid_pdf(content_type, body, ok, passes):
    app = Mock()
    app.results = []
    app.page.url = 'https://qa.example/release-notes-pdf'
    app.ui.visible.return_value.get_attribute.return_value = '/notes.pdf'
    response = app.page.request.get.return_value
    response.ok, response.headers = ok, {'content-type': content_type}
    response.body.return_value = body
    if passes:
        static_pages.verify_release_notes_content(app)
        app.page.request.get.assert_called_once_with('https://qa.example/notes.pdf')
        app.verify_static_data.assert_called_once_with('ReleaseNotesPage')
    else:
        with pytest.raises(AssertionError):
            static_pages.verify_release_notes_content(app)


@pytest.mark.parametrize('text,missing', [('  USER\nGUIDE   TITLE  ', False), ('Different document', True)])
def test_user_guide_compares_pdf_text_with_workbook_expectations(tmp_path, monkeypatch, text, missing):
    import openpyxl
    import pypdf
    app = Mock()
    app.NAME, app.STATIC_DATA_EXCEL = 'C3DC', 'C3DC_StaticData.xlsx'
    app.output_dir, app.results = tmp_path, []
    app._user_guide_pdf_url = 'https://qa.example/user-guide.pdf'
    response = app.page.request.get.return_value
    response.ok, response.headers = True, {'content-type': 'application/pdf'}
    response.body.return_value = b'%PDF-1.7 fixture'
    document = Mock()
    document.pages = [Mock()]
    document.pages[0].extract_text.return_value = text
    monkeypatch.setattr(pypdf, 'PdfReader', lambda stream: document)
    workbook = Mock()
    workbook.__getitem__ = Mock(return_value=Mock())
    workbook['UserGuidePage'].iter_rows.return_value = [('DocumentTitle', 'User Guide Title', None)]
    monkeypatch.setattr(openpyxl, 'load_workbook', lambda *a, **kw: workbook)

    static_pages.verify_user_guide_content(app)

    assert app._fail.called == missing
    workbook.close.assert_called_once_with()
    assert (tmp_path / 'user_guide.pdf').read_bytes() == b'%PDF-1.7 fixture'
    app.open_cohort_analyzer.assert_not_called()


@pytest.mark.parametrize('number,page,sheet', [
    (5, 'NotesToUser', 'NotesToUserPage'),
    (6, 'ExploreUserGuide', 'ExploreUserGuidePage'),
])
def test_explore_static_cases_open_explore_and_use_their_own_sheet(number, page, sheet):
    app = Mock(spec=C3DC)
    run_testcase_excel(app, ROOT / f'Testcases/C3DC/static/TC{number:02}_C3DC_Verify_{page}_Content.xlsx')
    assert [call[0] for call in app.method_calls] == ['accept_banner', 'open_explore', 'verify_explore_help_content', 'assert_no_failures']
    app.verify_explore_help_content.assert_called_once_with(sheet)


@pytest.mark.parametrize('sheet', ['NotesToUserPage', 'ExploreUserGuidePage'])
def test_explore_help_uses_scoped_controls_and_verifies_close(sheet):
    from unittest.mock import patch, call
    app = Mock()
    with patch('playwright.sync_api.expect') as expect:
        static_pages.verify_explore_help_content(app, sheet)
    prefix = f'Static/{sheet}/'
    assert app.click.call_args_list == [call(prefix + 'Open'), call(prefix + 'Close')]
    app.verify_static_data.assert_called_once_with(sheet)
    expect.return_value.to_be_visible.assert_called_once_with(timeout=app.ui.timeout_ms)
    expect.return_value.not_to_be_visible.assert_called_once_with(timeout=app.ui.timeout_ms)
