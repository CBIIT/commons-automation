"""Application column semantics for the shared result-table sorting verifier."""
from Commons.table_sorting import SortRule, SortingOptions


# ---------------------------------------------------------------------------
# Numeric values, file sizes, and compound cells
# ---------------------------------------------------------------------------

def sorting_options(app, tab):
    from Commons.apps.ins.result_tabs import INSResultTabs
    rules = {name: SortRule(casefold=True) for name in INSResultTabs.EXPORTS[tab].headers}
    rules.update({name: SortRule(kind='number', missing=('', 'Not Reported'))
                  for name in ('Fiscal Year', 'Cited By', 'Relative Citation Ratio')})
    # INS places unavailable citation ratios before numeric values in ascending order.
    rules['Relative Citation Ratio'] = SortRule(kind='number', nulls_smallest=True)
    rules.update({'Program(s)': SortRule(casefold=True, separator=';'), 'Project(s)': SortRule(casefold=True, separator=';')})
    rules['Size'] = SortRule(kind='size', missing=('', 'Not Reported'))
    return SortingOptions(rules=rules)
