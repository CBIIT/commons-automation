"""CCDI publication source parsing, UI verification and review reporting.

The supplied workbook is a release tracker, not an approved full UI snapshot.
Fold release rows by ID in sheet order; later releases replace earlier versions.
Draft/tracking sheets and entries explicitly marked Potential/Duplicate are not
promoted into expectations. Comparisons remain REVIEW items until approved.
"""
from collections import Counter
from datetime import date, datetime
from difflib import SequenceMatcher
import html
import json
import math
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import openpyxl
from playwright.sync_api import Error as PlaywrightError, expect

from Commons import action_log, excel_writer
from Commons.settings import input_dir


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


class PublicationsPage:
    """Publication Excel actions using the CCDI app's browser and result storage."""

    # --- Publication controls and baseline review ---

    def _publication_check(self, name, check):
        """Record a publication-control result without changing other app checks."""
        try:
            detail = check() or ""
            self.results.append({"check": f"Publications {name}", "status": "PASSED", "detail": detail})
            status = "PASSED"
        except (PlaywrightError, AssertionError, ValueError, KeyError) as err:
            detail, status = str(err), "FAILED"
            self._fail(f"Publications {name}: {detail}")
        with action_log.pytest_table_output_live():
            print(f"[Publications] {name}: {status}\n  {detail.splitlines()[0] if detail else ''}", flush=True)

    def load_publications_source(self, filename):
        """Load the release tracker for review, without approving UI differences."""
        path = Path(input_dir(self.NAME)) / filename
        self._publications_source = load_release_publications(path)
        self._publications_categories = {}
        self._publications_searches = {}
        self._publications_source_path = str(path)
        with action_log.pytest_table_output_live():
            print(f"[Publications source] {len(self._publications_source['records'])} released IDs; {self._publications_source['counts']}; {len(self._publications_source['excluded'])} explicitly excluded rows", flush=True)

    def _publication_count(self):
        text = self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first.inner_text()
        return int(text.replace(",", "").strip())

    def select_publication_category(self, category):
        """Select a category using desktop tabs or the responsive dropdown."""
        assert category in ("All", "Primary", "Secondary", "Abstracts"), category
        assert urlsplit(self.page.url).path == "/publications", f"Not on /publications: {self.page.url}"
        tab = self.ui.visible(self.repo.xpath(f"Publications/{category}Tab"))
        if tab.count():
            tab.first.click()
            expect(tab.first).to_have_class(re.compile("tabListItemActive"))
        else:
            self.page.locator(".tabDropdownItem.first:visible").click()
            self.ui.visible(f"//li[normalize-space()='{category}']").first.click()
            expect(self.page.locator(".tabDropdownItem.first:visible")).to_contain_text(category)
        count = self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first
        expect(count).to_have_text(re.compile(r"^[\d,]+$"))
        if self._publication_count():
            expect(self.page.locator('nav[aria-label="pagination navigation"] button[aria-current="true"]')).to_have_text("1")

    def _read_publication_page(self):
        """Read card fields from the rendered DOM, including the real Read More href."""
        records = self.page.locator(".publicationsItem").evaluate_all("""cards => cards.map(card => {
            const text = selector => (card.querySelector(selector)?.textContent || '').trim();
            const meta = Array.from(card.querySelectorAll('.publicationsItemConference')).map(e => ({
                type:(e.querySelector('.publicationsText2')?.textContent || '').trim(),
                value:(e.querySelector('.publicationsItemConferenceLink')?.textContent || '').trim()
            }));
            const main = meta.find(m => m.type !== 'PMID') || {};
            return {id:card.id, title:text('.publicationsItemTitle'), date:text('.publicationsItemDate'),
                type:main.type || '', venue:main.value || '', pmid:meta.find(m => m.type === 'PMID')?.value || '',
                tags:Array.from(card.querySelectorAll('.publicationsItemTag')).map(e => e.textContent.trim()),
                summary:(card.querySelector('.publicationsItemContent')?.innerText || '').trim(),
                url:card.querySelector('a.readMoreButtonContainer')?.getAttribute('href') || '', category:''};
        })""")
        for record in records:
            for key in ("id", "title", "date", "type", "venue", "pmid", "summary"):
                record[key] = normalize(record[key])
            record["tags"] = sorted(normalize(v) for v in record["tags"])
            assert record["id"] and record["title"], "A publication card has no ID/title"
            assert urlsplit(record["url"]).scheme in ("http", "https"), f"Invalid Read More URL: {record['id']}"
        return records

    def _collect_publication_pages(self):
        """Traverse every result page; fail on repeated IDs, gaps or wrong page sizes."""
        total = self._publication_count()
        if total == 0:
            expect(self.page.locator(".publicationsItem")).to_have_count(0)
            return []
        self.page.locator(".publicationsItem").first.wait_for(state="visible")
        first = self._read_publication_page()
        size = len(first)
        assert 0 < size <= total, f"{size} cards for {total} results"
        pages = math.ceil(total / size)
        assert pages <= 200, f"Unexpected pagination size: {pages} pages"
        records, seen = [], set()
        for number in range(1, pages + 1):
            if number > 1:
                previous_id = self.page.locator(".publicationsItem").first.get_attribute("id")
                button = self.page.locator('nav[aria-label="pagination navigation"] button').filter(has_text=re.compile(fr"^{number}$"))
                button.click()
                expect(button).to_have_attribute("aria-current", "true")
                self.page.wait_for_function("previous => document.querySelector('.publicationsItem')?.id !== previous", arg=previous_id, timeout=10000)
            current = first if number == 1 else self._read_publication_page()
            wanted_size = size if number < pages else total - size * (pages - 1)
            assert len(current) == wanted_size, f"Page {number}: {len(current)} cards; expected {wanted_size}"
            assert self._publication_count() == total, "Result count changed while paginating"
            for record in current:
                assert record["id"] not in seen, f"Repeated publication {record['id']} on page {number}"
                seen.add(record["id"])
                records.append(record)
            with action_log.pytest_table_output_live():
                print(f"[Publications page] {number}/{pages}: {len(current)} cards", flush=True)
        assert len(records) == total, f"Collected {len(records)} cards; displayed count is {total}"
        return records

    def verify_publications_category(self, category):
        def check():
            self.select_publication_category(category)
            records = self._collect_publication_pages()
            if category != "All":
                for record in records:
                    record["category"] = category
            self._publications_categories[category] = records
            return f"{category}: {len(records)} unique cards; all pagination pages verified"
        self._publication_check(category, check)

    def verify_publications_partition(self):
        """Check that category results are disjoint and together match All."""
        def check():
            groups = self._publications_categories
            assert set(groups) == {"All", "Primary", "Secondary", "Abstracts"}, "A category was not collected"
            all_ids = {r["id"] for r in groups["All"]}
            combined = set()
            for category in ("Primary", "Secondary", "Abstracts"):
                ids = {r["id"] for r in groups[category]}
                assert not combined & ids, f"Category overlap in {category}: {combined & ids}"
                combined |= ids
            assert combined == all_ids, f"Category membership differs from All: {combined ^ all_ids}"
            return f"Primary + Secondary + Abstracts = All ({len(all_ids)} records), without duplicates"
        self._publication_check("category membership", check)

    def search_publications(self, keyword):
        """Type a keyword and explicitly click this page's Search button."""
        self.ui.visible(self.repo.xpath("Publications/SearchInput")).first.fill(keyword)
        self.submit_publications_search()

    def submit_publications_search(self):
        self.ui.visible(self.repo.xpath("Publications/SearchButton")).first.click()

    def clear_publications_search(self):
        """Clear the input; the next visible Excel step applies the empty search."""
        def check():
            self.ui.visible(self.repo.xpath("Publications/ClearSearch")).first.click()
            expect(self.ui.visible(self.repo.xpath("Publications/SearchInput")).first).to_have_value("")
            return "Search input cleared (results reset by the separate Search step)"
        self._publication_check("clear search input", check)

    def verify_publications_search(self, keyword, expected_id):
        def check():
            expect(self.ui.visible(self.repo.xpath("Publications/SearchInput")).first).to_have_value(keyword)
            assert expected_id in self._publications_source["records"], f"Expected search ID {expected_id} is not in the source workbook"
            self.page.wait_for_function("total => Number(document.querySelector('.totalNum').textContent.replaceAll(',', '')) < total", arg=len(self._publications_categories["All"]), timeout=15000)
            self.page.locator(f".publicationsItem[id='{expected_id}']").wait_for(state="visible", timeout=15000)
            records = self._collect_publication_pages()
            ids = {r["id"] for r in records}
            assert expected_id in ids, f"Search did not return expected publication {expected_id}"
            assert len(ids) < len(self._publications_categories["All"]), "Search did not narrow the publication list"
            previous = self._publications_searches.get(keyword.casefold())
            if previous is not None:
                assert previous == ids, "Case-only search change returned different publications"
            self._publications_searches[keyword.casefold()] = ids
            return f"'{keyword}': {len(ids)} results; expected publication found; case-insensitive results consistent"
        self._publication_check(f"search {keyword}", check)

    def verify_publications_reset(self):
        def check():
            expect(self.ui.visible(self.repo.xpath("Publications/SearchInput")).first).to_have_value("")
            expected = {r["id"] for r in self._publications_categories["All"]}
            expect(self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first).to_have_text(str(len(expected)), timeout=15000)
            ids = {r["id"] for r in self._read_publication_page()}
            assert ids <= expected and ids, "Reset results are not from All publications"
            return f"Empty search restores All ({len(expected)} results)"
        self._publication_check("reset results", check)

    def verify_empty_publications_search(self):
        def check():
            expect(self.ui.visible(self.repo.xpath("Publications/ResultsCount")).first).to_have_text("0")
            expect(self.page.locator(".publicationsItem")).to_have_count(0)
            return "No-match search shows 0 results and no stale cards"
        self._publication_check("no-match search", check)

    def write_publication_results(self):
        """Save observed records and review differences; never approve a baseline."""
        groups = self._publications_categories
        observed = {r["id"]: dict(r) for r in groups.get("All", [])}
        for category in ("Primary", "Secondary", "Abstracts"):
            for record in groups.get(category, []):
                if record["id"] in observed:
                    observed[record["id"]]["category"] = category
        source = self._publications_source
        differences = review_publications(source, observed)
        review = {"status": "PENDING USER CONFIRMATION", "url": self.page.url,
            "source_path": self._publications_source_path, "source": source, "observed": observed,
            "ui_counts": {category: len(records) for category, records in groups.items()}, "differences": differences,
            "id_candidates": publication_id_candidates(source, observed)}
        (self.output_dir / "Publications_Baseline_Review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False))
        headers = ["ID", "Title", "Category", "Date", "Type", "Venue", "PMID", "Tags", "Read More URL", "Visible summary"]
        for category, records in groups.items():
            excel_writer.write_sheet(self.output_dir / "Output_CCDI_Publications.xlsx", category, headers,
                [[r["id"], r["title"], category, r["date"], r["type"], r["venue"], r["pmid"], ", ".join(r["tags"]), r["url"], r["summary"]] for r in records])
        with action_log.pytest_table_output_live():
            print(f"[Publications review] {len(source['records'])} workbook IDs; {len(observed)} UI IDs; {len(differences)} review items. Expected data has NOT been updated or approved.", flush=True)
