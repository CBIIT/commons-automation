"""Application column semantics for the shared result-table sorting verifier."""
from Commons.table_sorting import SortRule, SortingOptions


# ---------------------------------------------------------------------------
# Case Files request fields (singular/plural IDs differ between UI releases)
# ---------------------------------------------------------------------------

CASE_FILE_SORT_FIELDS = {
    'File Name': ('file_name',),
    'Access': ('access_file',),
    'Format': ('file_format',),
    'File Type': ('file_type',),
    'Size': ('file_size',),
    'Association': ('association', 'file_association'),
    'Description': ('file_description',),
    'Sample ID': ('sample_id', 'sample_ids'),
    'Case ID': ('case_id', 'case_ids'),
    'Breed': ('breed',),
    'Diagnosis': ('diagnosis',),
    'File UUID': ('file_uuid',),
    'Study Code': ('study_code',),
}


# ---------------------------------------------------------------------------
# Numeric values, file sizes, and compound cells
# ---------------------------------------------------------------------------

def sorting_options(app, tab):
    from Commons.apps.icdc.result_tabs import ICDCResultTabs
    rules = {name: SortRule(nulls_smallest=True) for name in ICDCResultTabs.EXPORTS[tab].headers}
    rules.update({name: SortRule(kind='number', nulls_smallest=True,
                                missing=('', 'Not Determined', 'Not Reported', 'Not Applicable', 'Unknown'))
                  for name in ('Age', 'Weight (kg)')})
    # The model indexes this field as a keyword with categorical missing-value labels.
    rules['Percentage Tumor'] = SortRule(nulls_smallest=True)
    rules['Size'] = SortRule(kind='size', missing=('', 'Not Reported'))
    if tab != 'Case Files':
        return SortingOptions(rules=rules)

    # -----------------------------------------------------------------------
    # Match the requested sort and first page; then wait for its rows to render
    # -----------------------------------------------------------------------
    def response_matches(response, name, direction):
        if 'graphql' not in response.url or response.request.method != 'POST':
            return False
        payload = response.request.post_data_json
        if not isinstance(payload, dict):
            return False
        variables = payload.get('variables') or {}
        return (payload.get('operationName') == 'getFilesOverview'
                and variables.get('file_level') == ['case']
                and variables.get('offset', 0) == 0
                and variables.get('order_by') in CASE_FILE_SORT_FIELDS[name]
                and variables.get('sort_direction') == direction)

    def response_ids(response):
        payload = response.json()
        if payload.get('errors'):
            raise AssertionError('; '.join(error['message'] for error in payload['errors']))
        records = (payload.get('data') or {}).get('fileOverview')
        assert isinstance(records, list), 'ICDC Case Files sort response has no fileOverview records'
        identities = [record.get('file_name') for record in records]
        assert all(isinstance(value, str) and value for value in identities), \
            'ICDC Case Files sort response has missing file names'
        return identities

    return SortingOptions(rules=rules, identity_column='File Name',
                          response_matches=response_matches, response_ids=response_ids)
