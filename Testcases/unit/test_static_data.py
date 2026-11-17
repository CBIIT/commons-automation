"""Static content keeps strict text checks and optional embedded-content attributes."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from Commons.static_data import verify_static_page

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('attribute_header', ['verificationAttribute', 'Notes'])
@pytest.mark.parametrize('attribute,actual,expected,passes', [
    ('', 'Original page text', 'Original page text', True),
    ('', 'Changed page text', 'Original page text', False),
    ('title', 'Data Model Navigator', 'Data Model Navigator', True),
    ('src', 'https://viewer.example/?config=model', 'https://viewer.example/?config=model', True),
    ('src', 'https://wrong.example/', 'https://viewer.example/?config=model', False),
    ('title', None, 'Data Model Navigator', False),
])
def test_static_value_verification(monkeypatch, tmp_path, attribute_header, attribute, actual, expected, passes):
    sheet = Mock()
    sheet.iter_rows.return_value = iter([
        ('TabName', 'verificationText', 'verificationUrl', attribute_header),
        ('Content', expected, None, attribute),
    ])
    workbook = {'Page': sheet}
    class Workbook(dict):
        sheetnames = ['Page']

        def close(self):
            pass
    monkeypatch.setattr('Commons.static_data.openpyxl.load_workbook', lambda *a, **kw: Workbook(workbook))
    monkeypatch.setattr('Commons.static_data.excel_writer.write_sheet', Mock())
    element = Mock()
    element.inner_text.return_value = actual
    element.get_attribute.return_value = actual
    app = SimpleNamespace(NAME='GC', STATIC_DATA_EXCEL='GC_StaticData.xlsx',
                          output_dir=tmp_path, settings=SimpleNamespace(env='qa2'),
                          repo=Mock(), ui=Mock())
    app.ui.loc.return_value.first = element

    problems = verify_static_page(app, 'Page')

    assert (not problems) == passes
    if attribute and attribute_header == 'verificationAttribute':
        element.inner_text.assert_not_called()
        element.get_attribute.assert_called_once_with(attribute)
    else:
        element.inner_text.assert_called_once()
        element.get_attribute.assert_not_called()
