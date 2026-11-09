"""CCDI publication source parsing and review comparisons (no browser/DB access).

The supplied workbook is a release tracker, not an approved full UI snapshot.
Fold release rows by ID in sheet order; later releases replace earlier versions.
Draft/tracking sheets and entries explicitly marked Potential/Duplicate are not
promoted into expectations. Comparisons remain REVIEW items until approved.
"""
from collections import Counter
from datetime import date, datetime
from difflib import SequenceMatcher
import html
import re
from urllib.parse import unquote, urlsplit

import openpyxl


def normalize(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    value = html.unescape(str(value)).replace("\\n", " ")
    value = value.translate(str.maketrans({"\u00a0": " ", "\u202f": " ", "\u200b": "", "\u2060": "", "\ufeff": "", "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "‑": "-", "‐": "-"}))
    return re.sub(r"\s+", " ", value).strip()


def category_name(value):
    value = normalize(value)
    return "Abstracts" if value.lower() in ("abstract", "abstracts") else value.title()


def tag_values(value):
    return sorted(normalize(v) for v in re.split(r"[,;]", value or "") if normalize(v))


def load_release_publications(path):
    """Read ID-bearing release sheets, preserving provenance and exclusions."""
    wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
    records, excluded, releases = {}, [], []
    try:
        for sheet in wb:
            if not (re.fullmatch(r"2\.\d+\.\d+", sheet.title) or sheet.title in ("Nov2025", "Apr2026")):
                continue
            releases.append(sheet.title)
            for cells in list(sheet.iter_rows())[1:]:
                values = [c.value for c in cells]
                if len(values) < 13 or not values[2] or not values[3] or not values[4]:
                    continue
                status = normalize(values[0])
                publication_id = normalize(values[2])
                if status.lower().startswith(("potential", "duplicate")):
                    excluded.append({"id": publication_id, "sheet": sheet.title, "row": cells[0].row, "reason": status})
                    continue
                category = category_name(values[4])
                if category not in ("Primary", "Secondary", "Abstracts"):
                    excluded.append({"id": publication_id, "sheet": sheet.title, "row": cells[0].row, "reason": f"Unresolved category: {category}"})
                    continue
                link = normalize(values[6])
                if not link.startswith(("https://", "http://")) and cells[6].hyperlink:
                    target = cells[6].hyperlink.target or ""
                    if target.startswith(("https://", "http://")):
                        link = target
                display_date = values[8]
                if isinstance(display_date, (date, datetime)):
                    display_date = display_date.strftime("%B %Y")
                records[publication_id] = {
                    "id": publication_id, "title": normalize(values[3]), "category": category,
                    "tags": tag_values(normalize(values[5])), "url": link,
                    "date": normalize(display_date), "type": normalize(values[9]),
                    "venue": normalize(values[10]), "pmid": normalize(values[11]),
                    "summary": normalize(values[12]), "sort_date": str(values[7] or ""),
                    "source_sheet": sheet.title, "source_row": cells[0].row, "status": status,
                }
    finally:
        wb.close()
    if not records:
        raise ValueError(f"No released publication rows found in {path}")
    return {"records": records, "excluded": excluded, "release_sheets": releases,
            "counts": dict(Counter(r["category"] for r in records.values()))}


def summary_matches(actual, expected):
    """Accept the UI's explicit ellipsis truncation, not arbitrary missing text."""
    actual, expected = normalize(actual), normalize(expected)
    if actual == expected:
        return True
    prefix = actual[:-3] if actual.endswith("...") else actual[:-1] if actual.endswith("…") else ""
    return len(prefix) >= 20 and expected.startswith(prefix)


def publication_urls_match(actual, expected):
    actual, expected = unquote(normalize(actual)), unquote(normalize(expected))
    # Older tracker rows supply only a PDF filename, not a full hosting URL.
    if not expected.startswith(("http://", "https://")):
        return bool(expected) and urlsplit(actual).path.rsplit("/", 1)[-1] == expected
    return actual.rstrip("/") == expected.rstrip("/")


def review_publications(source, observed):
    """Return review differences without updating or approving expected values."""
    expected = source["records"]
    differences = []
    for publication_id in sorted(set(expected) | set(observed)):
        want, got = expected.get(publication_id), observed.get(publication_id)
        if want is None or got is None:
            record = got or want
            differences.append({"id": publication_id, "title": record["title"],
                "kind": "UI only" if want is None else "Workbook only", "field": "record",
                "expected": "" if want is None else want["title"], "actual": "" if got is None else got["title"],
                "source_sheet": "" if want is None else want["source_sheet"], "source_row": "" if want is None else want["source_row"]})
            continue
        for field in ("title", "category", "date", "type", "venue", "pmid", "tags", "url", "summary"):
            before, after = want[field], got[field]
            matches = summary_matches(after, before) if field == "summary" else publication_urls_match(after, before) if field == "url" else sorted(before) == sorted(after) if field == "tags" else normalize(after) == normalize(before)
            if not matches:
                differences.append({"id": publication_id, "title": got["title"], "kind": "Field difference", "field": field,
                    "expected": before, "actual": after, "source_sheet": want["source_sheet"], "source_row": want["source_row"],
                    "note": "Preprints currently omit venue and PMID on the UI; confirm the intended display rule." if got["type"] == "Preprint" and field in ("venue", "pmid") else "Case-only difference in metadata rendered uppercase." if field == "venue" and normalize(before).casefold() == normalize(after).casefold() else ""})
    return differences


def publication_id_candidates(source, observed):
    """Suggest possible old/new IDs for human review, never auto-merge them."""
    expected = source["records"]
    additions = {key: record for key, record in observed.items() if key not in expected}
    candidates = []
    for old_id, old in expected.items():
        if old_id in observed or not additions:
            continue
        scores = [(SequenceMatcher(None, old["title"].casefold(), new["title"].casefold()).ratio(), key, new) for key, new in additions.items()]
        score, new_id, new = max(scores, key=lambda item: item[0])
        old_prefix = old["title"].split(":", 1)[0].casefold()
        new_prefix = new["title"].split(":", 1)[0].casefold()
        if score >= .65 or (len(old_prefix) > 5 and old_prefix == new_prefix):
            candidates.append({"source_id": old_id, "ui_id": new_id, "source_title": old["title"], "ui_title": new["title"],
                "similarity": round(score, 3), "source_sheet": old["source_sheet"], "source_row": old["source_row"],
                "decision": "Possible replacement/version update — confirm manually"})
    return candidates
