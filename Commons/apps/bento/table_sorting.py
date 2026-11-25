"""Application column semantics for the shared result-table sorting verifier."""
from Commons.table_sorting import SortRule, SortingOptions


# ---------------------------------------------------------------------------
# Numeric values, file sizes, and compound cells
# ---------------------------------------------------------------------------

def sorting_options(app, tab):
    rules = {name: SortRule(kind='number', missing=('', 'Not Reported')) for name in ('Recurrence Score', 'Tumor Size (cm)', 'Age (years)', 'Survival (days)')}
    rules['Size'] = SortRule(kind='size', missing=('', 'Not Reported'))
    return SortingOptions(rules=rules)
