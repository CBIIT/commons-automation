"""ICDC sorting readiness must belong to the requested column and page."""
from unittest.mock import Mock

import pytest

from Commons.apps.icdc.table_sorting import sorting_options

pytestmark = pytest.mark.unit


def sort_response(**overrides):
    variables = {'file_level': ['case'], 'offset': 0, 'order_by': 'sample_ids', 'sort_direction': 'asc'}
    variables.update(overrides)
    response = Mock(url='https://canine.test/v1/graphql/')
    response.request.method = 'POST'
    response.request.post_data_json = {'operationName': 'getFilesOverview', 'variables': variables}
    return response


@pytest.mark.parametrize('field', ['sample_id', 'sample_ids'])
def test_case_file_waiter_accepts_sample_id_request_variants(field):
    options = sorting_options(Mock(), 'Case Files')
    assert options.response_matches(sort_response(order_by=field), 'Sample ID', 'asc')
    assert options.identity_column == 'File Name'


@pytest.mark.parametrize('overrides', [
    {'order_by': 'file_name'}, {'sort_direction': 'desc'}, {'offset': 10}, {'file_level': ['study']},
])
def test_case_file_waiter_rejects_other_sorts_pages_and_file_scopes(overrides):
    options = sorting_options(Mock(), 'Case Files')
    assert not options.response_matches(sort_response(**overrides), 'Sample ID', 'asc')


def test_case_file_waiter_reads_response_order_and_rejects_graphql_errors():
    options = sorting_options(Mock(), 'Case Files')
    response = sort_response()
    response.json.return_value = {'data': {'fileOverview': [{'file_name': 'b.fastq'}, {'file_name': 'a.fastq'}]}}
    assert options.response_ids(response) == ['b.fastq', 'a.fastq']
    response.json.return_value = {'errors': [{'message': 'Sort failed'}]}
    with pytest.raises(AssertionError, match='Sort failed'):
        options.response_ids(response)
    response.json.return_value = {'data': {'fileOverview': [{'file_name': None}]}}
    with pytest.raises(AssertionError, match='missing file names'):
        options.response_ids(response)
