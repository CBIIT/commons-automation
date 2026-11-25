"""Application column semantics for the shared result-table sorting verifier."""
from Commons.table_sorting import SortRule, SortingOptions


# ---------------------------------------------------------------------------
# Numeric values, file sizes, and compound cells
# ---------------------------------------------------------------------------

def sorting_options(app, tab):
    rules = {}
    rules['Size'] = SortRule(kind='size', missing=('', 'Not Reported'))
    return SortingOptions(rules=rules)
