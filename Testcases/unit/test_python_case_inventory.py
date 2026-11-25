"""Audit migrated coverage, data references, and valid adapter/filter contracts."""
from pathlib import Path
from functools import lru_cache
import inspect
import json
import runpy

import pytest

from Commons.apps import APPS
from Commons.object_repository import ObjectRepository
from Commons.settings import input_dir

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / 'docs/python_case_inventory.json').read_text())['cases']


class RecordingApp:
    output_dir = Path('/evidence')

    def __init__(self, calls, fixture='c3dc', name=None):
        self.calls, self.fixture, self.name = calls, fixture, name or fixture

    def __getattr__(self, name):
        return RecordingApp(self.calls, self.fixture, f'{self.name}.{name}')

    def __call__(self, *args, **kwargs):
        self.calls.append({'method': self.name, 'args': list(args), 'kwargs': kwargs})


def test_python_case_inventory_matches_reference():
    expected = {entry['python'] for entry in CASES}
    folders = {Path(entry['python']).parts[1] for entry in CASES}
    actual = {str(path.relative_to(ROOT)) for folder in folders
              for path in (ROOT / 'Testcases' / folder).rglob('test_*.py')}
    assert actual == expected
    for folder in folders:
        assert not list((ROOT / 'Testcases' / folder).rglob('TC*.xlsx'))


@lru_cache(maxsize=None)
def repository(app):
    return ObjectRepository(app)


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['python'])
def test_python_case_has_valid_inputs_filters_and_adapter_calls(case):
    calls = []
    fixture = case['fixture']
    app_type = APPS[case['app']]
    app = RecordingApp(calls, fixture)
    path = ROOT / case['python']
    testcase = runpy.run_path(str(path))[path.stem]
    assert {marker.name for marker in testcase.pytestmark} == set(case['markers'])
    testcase(app)
    assert calls[-1]['method'] == fixture + '.assert_no_failures'
    loads = [call['args'] for call in calls if call['method'] == fixture + '.load_query_file']
    expected_loads = [[case['input']]] if case['input'] and not case['input'].endswith('_StaticData.xlsx') else []
    assert loads == expected_loads
    if any(call['method'] == 'c3dc.open_cohort_analyzer' for call in calls):
        assert app._analyzer_output == app.output_dir / Path(case['reference']).stem
    if case['input']:
        assert (input_dir(case['app']) / case['input']).is_file()
    repo = repository(case['app'])
    for call in calls:
        parts = call['method'].split('.')[1:]
        owner = (app_type.FILE_CART_CLASS if parts[0] == 'file_cart' else
                 app_type.RESULT_TABS_CLASS if parts[0] == 'result_tabs' else app_type)
        method = getattr(owner, parts[-1])
        inspect.signature(method).bind(None, *call['args'], **call['kwargs'])
        if parts == ['select_filter']:
            group, value = call['args']
            assert repo.filter_group(group).checkbox_xpath(value)
        if parts == ['click']:
            assert repo.xpath(call['args'][0])
        if parts == ['load_publications_source']:
            assert (input_dir(case['app']) / call['args'][0]).is_file()
