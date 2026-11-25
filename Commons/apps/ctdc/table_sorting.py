"""Application column semantics for the shared result-table sorting verifier."""
from Commons.table_sorting import SortRule, SortingOptions
from Commons.result_tabs import category_text_matches


# ---------------------------------------------------------------------------
# Numeric values, file sizes, and compound cells
# ---------------------------------------------------------------------------

def sorting_options(app, tab):
    rules = {'Age at Enrollment': SortRule(kind='number', missing=('', 'Not Reported'))}
    rules['Specimen Record ID'] = SortRule(nulls_smallest=True)
    rules['Carcinogen Exposure'] = SortRule(nulls_smallest=True)
    rules['Size'] = SortRule(kind='size', missing=('', 'Not Reported'))
    if tab != 'Participants':
        return SortingOptions(rules=rules)

    # Preserve complete labels such as "Carboplatin, Pemetrexed, Amivantamab".
    fields = {'Race': 'race', 'Therapy': 'therapy_name',
              'Therapy Category': 'therapy_category', 'Best Response': 'best_response_to_therapy'}
    records = {}

    def remember(response):
        if 'graphql' not in response.url or response.request.method != 'POST':
            return
        if response.request.post_data_json.get('operationName') != 'participantOverview':
            return
        for record in (response.json().get('data') or {}).get('participantOverview') or []:
            records[record['participant_id']] = record

    app.page.on('response', remember)

    def clinical_values(name, identity, displayed):
        if name not in fields:
            return displayed
        assert identity in records, f'{name}: no complete reference values for {identity}'
        values = records[identity][fields[name]] or []
        assert isinstance(values, list) and all(isinstance(value, str) for value in values)
        assert category_text_matches(displayed, values), f'{name}: displayed labels differ from the data response'
        return values

    return SortingOptions(rules=rules, identity_column='Participant ID', cell_values=clinical_values)
