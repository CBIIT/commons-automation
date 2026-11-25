"""Verify C3DC study identity, description, counts and the manifest download.

Expected metadata/counts come from Memgraph. The input workbook supplies the
manifest URL. All studies write their checks to one consolidated Excel report.
"""
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import openpyxl
from playwright.sync_api import expect

from Commons import action_log, excel_writer


# ---------------------------------------------------------------------------
# Validation and text normalization
# ---------------------------------------------------------------------------


def validate_accession(accession):
    """Reject malformed IDs before using one in a URL or locator."""
    if not re.fullmatch(r"phs\d{6}", accession):
        raise ValueError(f"Invalid dbGaP accession: {accession!r}")
    return accession


def normalize_text(value):
    """Normalize whitespace so UI line wrapping does not cause text mismatches."""
    return re.sub(r"\s+", " ", str(value or "").replace("\u00a0", " ")).strip()


# ---------------------------------------------------------------------------
# Consolidated report setup
# ---------------------------------------------------------------------------


def begin_study_details_report(app, report_name="StudyDetails_AllStudies"):
    """Reset this testcase's results; never mix a previous run into the batch."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", report_name):
        raise ValueError(f"Invalid study-details report name: {report_name!r}")
    app._study_details_results = {}
    app._study_details_report_name = report_name


# ---------------------------------------------------------------------------
# Study Details page navigation
# ---------------------------------------------------------------------------


def open_study_details(app, accession):
    """Find the requested catalog row (including later pages), then click it."""
    validate_accession(accession)
    if urlsplit(app.page.url).path.rstrip("/") != "/studies":
        raise AssertionError("Open the Studies listing before open_study_details")
    # Returning via goto can finish before the catalog's API request. Do not
    # interpret its loading state as a missing accession or missing Next button.
    app.ui.wait_visible(app.repo.xpath("StudiesPage/Table"))
    for _ in range(app.MAX_PAGES):
        link = app.page.locator(f"a[href='/studies/{accession}']")
        if link.count():
            link.click()
            expect(app.page).to_have_url(re.compile(fr"/studies/{accession}$"))
            app.ui.visible(app.repo.xpath("StudyDetails/Name")).first.wait_for(state="visible")
            action_log.ui_action(f"Study details opened by clicking {accession} in the Studies listing.")
            return
        next_button = app.ui.visible(app.repo.xpath("StudiesPage/Next-Btn")).first
        if not next_button.is_enabled():
            break
        previous = app.page.locator("tbody tr").first.inner_text()
        next_button.click()
        expect(app.page.locator("tbody tr").first).not_to_have_text(previous)
    raise AssertionError(f"Study {accession} was not found in the Studies listing")


# ---------------------------------------------------------------------------
# Study Details page verification
# ---------------------------------------------------------------------------


class StudyDetailsVerifier:
    """Compare one C3DC study with Memgraph and verify its manifest download."""

    def __init__(self, app, accession):
        self.app, self.page = app, app.page
        self.accession = validate_accession(accession)
        self.rows = []

    # --- Page locators and result recording ---

    def get_locator(self, key):
        return self.app.ui.visible(self.app.repo.xpath(f"StudyDetails/{key}"))

    def record_check(self, field, expected, actual, *, passed=None):
        passed = expected == actual if passed is None else passed
        status = "PASSED" if passed else "FAILED"
        printable = lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value)
        self.rows.append([self.accession, field, printable(expected), printable(actual), status])
        with action_log.pytest_table_output_live():
            print(f"[Study details] {self.accession} / {field}\n  Expected: {printable(expected)}\n  Actual:   {printable(actual)}\n  Result: {status}", flush=True)
        if passed:
            self.app.results.append({"check": f"StudyDetails {field}", "status": status, "detail": printable(actual)})
        else:
            self.app._fail(f"StudyDetails {self.accession} {field}: expected {printable(expected)}; actual {printable(actual)}")

    def run_check_section(self, field, operation):
        """Record a section error so the next verification section can still run."""
        try:
            operation()
        except Exception as err:
            self.record_check(field, "Check completes successfully", str(err), passed=False)

    # --- Memgraph query execution ---

    def run_query(self, key):
        """Run a named workbook query with the study accession bound as a parameter."""
        query = self.app.query_file.query_for_tab(key)
        if "$accession" not in query:
            raise ValueError(f"{key} must bind $accession")
        action_log.memgraph_query(f"Study details {key} (accession={self.accession})", query)
        with self.app.connected_source().get_bolt_driver().session() as session:
            rows = [dict(r) for r in session.run(query, {"accession": self.accession})]
        return rows

    # --- Study metadata and overview counts ---

    def verify_metadata_and_counts(self):
        """Compare only the three study text fields and three Overview counts."""
        rows = self.run_query("StudyMetadata")
        if len(rows) != 1:
            raise AssertionError(f"Expected one study for {self.accession}; found {len(rows)}")
        self.expected = rows[0]
        counts = self.run_query("StudyCounts")
        if len(counts) != 1:
            raise AssertionError(f"Expected one counts row; found {len(counts)}")
        self.counts = counts[0]
        for field, key in (("Accession", "accession"), ("Name", "name"), ("Description", "description")):
            self.record_check(field, normalize_text(self.expected[key]), normalize_text(self.get_locator(field).first.inner_text()))
        for label in ("Participants", "Samples", "Files"):
            self.record_check(label, int(self.counts[label.lower()]), int(self.get_locator(label).first.inner_text().replace(",", "")))

    # --- Study manifest verification ---

    def get_expected_manifest_url(self):
        """Read this study's expected manifest URL from the input workbook."""
        wb = openpyxl.load_workbook(self.app.query_file.path, read_only=True, data_only=True)
        try:
            rows = iter(wb["Links"].values)
            headers = next(rows)
            links = [dict(zip(headers, row)) for row in rows]
        finally:
            wb.close()
        manifests = [link for link in links if link.get("Accession") == self.accession
                     and link.get("Label") == "Study Manifest" and link.get("Kind") == "download"]
        if len(manifests) != 1:
            raise ValueError(f"Expected one configured Study Manifest for {self.accession}; found {len(manifests)}")
        return manifests[0]["URL"]

    def verify_manifest(self):
        """Check the URL and filename, then save and open the downloaded Excel file.

        Require at least one nonempty cell. Manifest contents are not compared
        with database records.
        """
        expected_url = self.get_expected_manifest_url()
        link = self.get_locator("ManifestLink")
        expect(link).to_have_count(1)
        actual_url = link.get_attribute("href")
        self.record_check("Manifest URL", expected_url, actual_url)
        if actual_url != expected_url:
            return
        with self.page.expect_download(timeout=30000) as event:
            link.click()
        download = event.value
        name = Path(download.suggested_filename).name
        self.record_check("Manifest filename", unquote(urlsplit(expected_url).path.rsplit("/", 1)[-1]), name)
        if not name.lower().endswith(".xlsx"):
            raise AssertionError(f"Expected Excel manifest; got {name}")
        path = self.app.output_dir / name
        download.save_as(path)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            populated = any(any(cell is not None for cell in row)
                            for sheet in wb for row in sheet.iter_rows(values_only=True))
        finally:
            wb.close()
        self.record_check("Manifest download opens", True, populated)

    # --- Verification workflow ---

    def run(self):
        """Check metadata/counts and the manifest, then save consolidated results."""
        if self.app.query_file is None:
            raise ValueError("Load the study-details query workbook first")
        try:
            self.run_check_section("Study metadata and counts", self.verify_metadata_and_counts)
            self.run_check_section("Manifest download", self.verify_manifest)
        finally:
            self.write_consolidated_report()

    # --- Consolidated report output ---

    def write_consolidated_report(self):
        """Update the testcase's single Excel report after each study."""
        results = getattr(self.app, "_study_details_results", {})
        results[self.accession] = self.rows
        self.app._study_details_results = results
        all_rows = [row for rows in results.values() for row in rows]
        failures = [row for row in all_rows if row[-1] == "FAILED"]
        summaries = []
        for accession, rows in results.items():
            failed = [r for r in rows if r[-1] == "FAILED"]
            counts = {r[1]: r for r in rows if r[1] in ("Participants", "Samples", "Files")}
            summaries.append([accession, "FAILED" if failed else "PASSED", len(rows) - len(failed), len(failed),
                              *[counts[label][2] if label in counts else "" for label in ("Participants", "Samples", "Files")],
                              *[counts[label][3] if label in counts else "" for label in ("Participants", "Samples", "Files")],
                              "; ".join(r[1] for r in failed)])
        report_name = getattr(self.app, "_study_details_report_name", "StudyDetails_AllStudies")
        path = self.app.output_dir / f"{report_name}.xlsx"
        header = ["Accession", "Check", "Expected", "Actual", "Status"]
        excel_writer.write_sheet(path, "Summary", ["Accession", "Status", "Passed", "Failed", "DB Participants", "DB Samples", "DB Files", "UI Participants", "UI Samples", "UI Files", "Failed checks"], summaries, header_color=excel_writer.LISTING_HEADER_COLOR)
        excel_writer.write_sheet(path, "Mismatches", header, failures, header_color=excel_writer.LISTING_HEADER_COLOR)
        highlights = {(i, col) for i, row in enumerate(all_rows) if row[-1] == "FAILED" for col in (2, 3, 4)}
        excel_writer.write_sheet(path, "All Checks", header, all_rows, header_color=excel_writer.LISTING_HEADER_COLOR,
                                 highlight_cells=highlights)


# ---------------------------------------------------------------------------
# Public verification entry point
# ---------------------------------------------------------------------------


def verify_study_details(app, accession):
    """Excel testcase action: verify study text, counts and the manifest download."""
    StudyDetailsVerifier(app, accession).run()
