"""C3DC result-tab sort semantics and exact GraphQL response readiness."""
import re
from decimal import Decimal

from Commons.table_sorting import SortRule, SortingOptions
from Commons.apps.c3dc.result_tabs import category_text_matches


# ---------------------------------------------------------------------------
# API fields used by dynamically discovered Participants table headers
# ---------------------------------------------------------------------------

PARTICIPANT_SORT_FIELDS = {
    'Participant ID': 'participant_id', 'Sex at Birth': 'sex_at_birth',
    'Diagnosis': 'diagnosis', 'Diagnosis Category': 'diagnosis_category',
    'Age at Diagnosis (days)': 'age_at_diagnosis', 'Anatomic Site': 'diagnosis_anatomic_site',
    'Last Known Survival Status': 'last_known_survival_status',
    'Age at Last Known Survival Status': 'age_at_last_known_survival_status',
    'Treatment Type': 'treatment_type', 'Age at Treatment Start': 'age_at_treatment_start',
}

SORT_FIELDS = {
    'Participants': PARTICIPANT_SORT_FIELDS,
    'Studies': {
        'Grant ID': 'grant_id',
        'Number of Files': 'num_of_files',
        'Number of Participants': 'num_of_participants',
        'Number of Samples': 'num_of_samples',
        'Principal Investigator(s)': 'personnel_name',
        'PubMed ID': 'pubmed_id',
        'Study ID': 'study_id',
        'Study Name': 'study_name',
        'Study Phase': 'study_phase',
    },
    'Samples': {
        'Anatomic Site': 'anatomic_site',
        'Participant Age at Collection (days)': 'participant_age_at_collection',
        'Participant ID': 'participant_id',
        'Sample ID': 'sample_id',
        'Sample Tumor Status': 'sample_tumor_status',
        'Study ID': 'study_id',
        'Tumor Spatial Extent': 'tumor_spatial_extent',
    },
    'GeneticAnalysis': {
        'Alteration': 'alteration',
        'Genetic Analysis ID': 'genetic_analysis_id',
        'HGVS Genome': 'hgvs_genome',
        'Participant ID': 'participant_id',
        'Reported Significance': 'reported_significance',
        'Reported Significance System': 'reported_significance_system',
        'Status': 'status',
        'Study ID': 'study_id',
    },
    'Files': {
        'Age at Collection': 'participant_age_at_collection',
        'Anatomic Site': 'anatomic_site',
        'Data Category': 'data_category',
        'File Name': 'file_name',
        'File Type': 'file_type',
        'Participant ID': 'participant_id',
        'Sample ID': 'sample_id',
        'Sample Tumor Status': 'sample_tumor_status',
        'Study ID': 'study_id',
        'Tumor Spatial Extent': 'tumor_spatial_extent',
    },
    'ImagingData': {
        'Fixation/Embedding Method': 'fixation_embedding_method',
        'IDC Histopathology Viewer': 'slim_url',
        'Image Modality': 'image_modality',
        'Magnification': 'magnification',
        'Participant ID': 'participant_id',
        'Sample ID': 'sample_id',
        'Series UID': 'series_uid',
        'Staining Method': 'staining_method',
        'Study ID': 'study_id',
        'Study UID': 'study_uid',
    },
}

# GraphQL operation, visible identity column, and API identity field.
SORT_RESPONSES = {
    'Participants': ('participantOverview', 'Participant ID', 'participant_id'),
    'Studies': ('studyOverview', 'Study ID', 'study_id'),
    'Samples': ('sampleOverview', 'Sample ID', 'sample_id'),
    'GeneticAnalysis': ('geneticAnalysisOverview', 'Genetic Analysis ID', 'genetic_analysis_id'),
    'Files': ('fileOverview', 'File Name', 'file_name'),
    'ImagingData': ('idcOverview', 'Series UID', 'series_uid'),
}

def sorting_options(app, tab):
    operation, identity_column, identity_field = SORT_RESPONSES[tab]
    reference_rows = {}

    # Multi-value keyword fields use minimum/maximum values; counts and ages stay numeric.
    array_columns = {
        'Participants': ('Diagnosis', 'Diagnosis Category', 'Anatomic Site', 'Treatment Type'),
        'Studies': ('PubMed ID', 'Principal Investigator(s)', 'Grant ID'),
        'Samples': ('Anatomic Site',),
        'GeneticAnalysis': (),
        'Files': ('Data Category', 'Participant ID', 'Sample ID', 'Anatomic Site',
                  'Sample Tumor Status', 'Tumor Spatial Extent'),
        'ImagingData': ('Participant ID', 'Sample ID'),
    }
    numeric_columns = {
        'Participants': ('Age at Diagnosis (days)', 'Age at Last Known Survival Status',
                         'Age at Treatment Start'),
        'Studies': ('Number of Participants', 'Number of Samples', 'Number of Files'),
        'Samples': ('Participant Age at Collection (days)',),
        'GeneticAnalysis': (), 'Files': ('Age at Collection',), 'ImagingData': (),
    }
    rules = {name: SortRule(separator=';') for name in array_columns[tab]}
    rules.update({name: SortRule(kind='number', separator=';', missing=('', 'Not Reported'))
                  for name in numeric_columns[tab]})
    if tab == 'Samples':
        # The model indexes unknown collection ages as -999, rather than a missing field.
        rules['Participant Age at Collection (days)'] = SortRule(
            kind='number', missing=('', 'Not Reported'), unknown_number=Decimal(-999))

    if tab == 'Files':
        rules['Data Category'] = SortRule(separator=',')
        rules['Age at Collection'] = SortRule(
            kind='number', separator=';', missing=('', 'Not Reported'))

    # Match this exact field's response, never a pending response from a previous column.
    def response_matches(response, name, direction):
        if '/v1/graphql' not in response.url or response.request.method != 'POST':
            return False
        payload = response.request.post_data_json
        return (payload.get('operationName') == operation
                and payload.get('variables', {}).get('order_by') == SORT_FIELDS[tab][name]
                and payload.get('variables', {}).get('sort_direction') == direction)

    def response_ids(response):
        payload = response.json()
        if payload.get('errors'):
            message = '; '.join(error['message'] for error in payload['errors'])
            mapping_error = re.search(r'No mapping found for \[[^\]]+\] in order to sort on', message)
            raise AssertionError(mapping_error.group() if mapping_error else message[:500])
        records = payload['data'][operation]
        reference_rows.update({row[identity_field]: row for row in records})
        return [row[identity_field] for row in records]

    def study_values(name, identity, displayed):
        # Commas inside names/credentials cannot be used to split displayed lists.
        fields = {'Principal Investigator(s)': 'personnel_name', 'PubMed ID': 'pubmed_id', 'Grant ID': 'grant_id'}
        if name not in fields:
            return displayed
        values = reference_rows[identity][fields[name]] or []
        assert isinstance(values, list) and all(isinstance(value, str) for value in values)
        assert category_text_matches(displayed, values), f'{name}: displayed values differ from the sort response'
        return values

    return SortingOptions(rules=rules, identity_column=identity_column,
                          response_matches=response_matches, response_ids=response_ids,
                          link_columns=('IDC Histopathology Viewer',) if tab == 'ImagingData' else (),
                          cell_values=study_values if tab == 'Studies' else None)
