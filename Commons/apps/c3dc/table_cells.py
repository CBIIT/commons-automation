"""Read complete C3DC file metadata when a table cell offers View All."""
from functools import lru_cache

from Commons.object_repository import ObjectRepository


@lru_cache(maxsize=1)
def _locators():
    return ObjectRepository('C3DC')


def read_file_cell(ui, cell_xpath: str) -> str:
    """Expand truncated lists, check their result count, and close the popup."""
    text = ui.text(cell_xpath)
    if 'View All' not in text:
        return text.replace('\n', '; ')

    repo = _locators()
    ui.loc(cell_xpath).locator('xpath=' + repo.xpath('ResultTabs/FileCellViewAll-Link')).click()
    dialog = ui.loc(repo.xpath('ResultTabs/FileCellValues-Dialog'))
    dialog.wait_for(state='visible')
    try:
        values = ui.loc(repo.xpath('ResultTabs/FileCellValues-Items')).all_text_contents()
        count = int(ui.text(repo.xpath('ResultTabs/FileCellValues-Count')).replace(',', '').strip())
        if len(values) != count:
            raise AssertionError(f'Expanded C3DC file cell has {len(values)} values; expected {count}.')
        return '; '.join(value.strip() for value in values)
    finally:
        ui.click(repo.xpath('ResultTabs/FileCellValues-Close'))
        dialog.wait_for(state='hidden')


def resolve_file_name_aliases(ui_table, expected) -> int:
    """Accept a displayed name only when its GUID-grouped database row contains it.

    Shared file GUIDs can have several datamodel nodes with different names.
    Queries return that complete name list as JSON; ordinary names stay scalar.
    Other columns remain unchanged and go through the normal comparison.
    """
    import json
    from Commons.compare import normalize_list

    if not expected.header or expected.header[0] != 'File Name':
        return 0
    remaining = list(ui_table.rows)
    resolved = 0
    for row in expected.rows:
        if not row or not str(row[0]).startswith('['):
            continue
        try:
            names = json.loads(row[0])
        except (TypeError, ValueError):
            continue
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            continue
        candidates = [actual for actual in remaining if actual and actual[0] in names]
        if len(candidates) > 1:
            candidates = [actual for actual in candidates if
                          [normalize_list(v) for v in actual[1:]] ==
                          [normalize_list(v) for v in row[1:]]]
        if len(candidates) == 1:
            actual = candidates[0]
            row[0] = actual[0]
            remaining.remove(actual)
            resolved += 1
    return resolved


def resolve_ranked_cells(ui_table, expected) -> int:
    """Validate top-N cells by counts, allowing any ordering/selection within a tie."""
    import json
    import re

    if 'Study ID' not in ui_table.header or 'Study ID' not in expected.header:
        return 0
    actual_by_study = {row[ui_table.header.index('Study ID')]: row for row in ui_table.rows}
    resolved = 0
    for row in expected.rows:
        actual = actual_by_study.get(row[expected.header.index('Study ID')])
        if actual is None:
            continue
        for column, value in enumerate(row):
            if not isinstance(value, str) or not value.startswith('{'):
                continue
            try:
                ranked = json.loads(value)
                items, limit = ranked['ranked_items'], ranked['top_n']
                counts = {}
                for item in items:
                    match = re.fullmatch(r'(.+) \((\d+)\)', item)
                    if match is None:
                        raise ValueError('Invalid source ranking')
                    counts[match[1]] = int(match[2])
                if not isinstance(limit, int) or limit < 1 or len(counts) != len(items):
                    continue
            except (TypeError, ValueError, KeyError):
                continue
            shown = [line.strip() for line in actual[column].splitlines() if line.strip()]
            more = bool(shown and shown[-1] == 'Read More')
            if more:
                shown.pop()
            names, values = [], []
            for item in shown:
                match = re.fullmatch(r'(.+) \((\d+)\)', item)
                if match is None or counts.get(match[1]) != int(match[2]):
                    break
                names.append(match[1])
                values.append(int(match[2]))
            else:
                # Every displayed value must have the correct count and ranking;
                # tied items can trade places, including at the top-N boundary.
                if (len(names) == len(set(names)) and
                        values == sorted(counts.values(), reverse=True)[:limit] and
                        more == (len(items) > limit)):
                    row[column] = actual[column]
                    resolved += 1
    return resolved
