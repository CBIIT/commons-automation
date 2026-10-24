"""
Pytest HTML suite report (one module: hooks, step capture, and HTML).

Turn on in gitignored .env (any of these keys, value true / 1 / yes / on):

  HTML_REPORT=true
  HTML_Report=true

After a suite run (not -m unit, not pytest -n):

  Reports/<SuiteSlug>_YYYYMMDD_HHMMSS.html
  Reports/latest.html

Suite slug comes from pytest -m, e.g. ``gc and quickrun`` → ``GC_quickrun``.
"""
from __future__ import annotations

import html
import os
import platform
import re
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

import pytest

from Commons.apps.base import BaseApp
from Commons.settings import ROOT

# ---------------------------------------------------------------------------
# Paths and flags
# ---------------------------------------------------------------------------

REPORTS_DIR = ROOT / "Reports"
SCREENSHOT_DIR = REPORTS_DIR / "screenshots"

_FLAG_KEYS = ("HTML_REPORT", "HTML_Report", "html_report")
_APP_MARKERS = frozenset({"gc", "c3dc", "ccdi", "icdc", "ctdc"})
_SUITE_MARKERS = frozenset({"smoke", "regression", "quickrun", "static"})

_stash_key = pytest.StashKey["HtmlReportSession"]()
_item_map_key = pytest.StashKey[dict]()
_active_config: Optional[pytest.Config] = None
_hooks_installed = False


def _truthy(raw: str) -> bool:
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def html_report_enabled() -> bool:
    """True when HTML_REPORT / HTML_Report is set in the environment (.env or shell)."""
    for key in _FLAG_KEYS:
        if key in os.environ and _truthy(os.environ[key]):
            return True
    return False


def format_duration_hms(seconds: float) -> str:
    """Always hours, minutes, and fractional seconds: 0h 1m 41.8s."""
    total = max(0.0, float(seconds))
    hours = int(total // 3600)
    rem = total - hours * 3600
    minutes = int(rem // 60)
    secs = rem - minutes * 60
    return f"{hours}h {minutes}m {secs:.1f}s"


def suite_slug_from_markexpr(markexpr: str) -> str:
    """``gc and quickrun`` → ``GC_quickrun``."""
    expr = (markexpr or "").strip()
    if not expr:
        return "Run"
    tokens: List[str] = []
    for part in re.split(r"\s+and\s+", expr, flags=re.IGNORECASE):
        token = part.strip().strip('"').strip("'")
        if not token:
            continue
        low = token.lower()
        if low in _APP_MARKERS:
            tokens.append(low.upper())
        elif low in _SUITE_MARKERS:
            tokens.append(low)
        else:
            tokens.append(re.sub(r"[^\w]+", "_", token).strip("_") or "tag")
    return "_".join(tokens) if tokens else "Run"


# ---------------------------------------------------------------------------
# Step capture (wraps Commons.action_log; no edits to that module)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReportStep:
    """One expandable row in the HTML execution log."""

    summary: str
    detail: str = ""
    status: str = "PASSED"


_steps: List[ReportStep] = []
_pagination_pending: int = 0


def clear_steps() -> None:
    global _pagination_pending
    _steps.clear()
    _pagination_pending = 0


def current_steps() -> List[ReportStep]:
    _flush_pagination()
    return list(_steps)


def _add_step(summary: str, detail: str = "", status: str = "PASSED") -> None:
    text = (summary or "").strip()
    if not text:
        return
    _flush_pagination()
    _steps.append(ReportStep(summary=text, detail=(detail or "").strip(), status=status.upper()))


def _is_pagination_key(repo_key: Optional[str]) -> bool:
    if not repo_key:
        return False
    low = repo_key.replace("\\", "/").lower()
    return "nextbtn" in low or "tabnext" in low


def _flush_pagination() -> None:
    global _pagination_pending
    if _pagination_pending <= 0:
        return
    count = _pagination_pending
    _pagination_pending = 0
    _steps.append(
        ReportStep(
            summary=f"[UI] Paginated result table ({count} additional page(s))",
            detail=(
                f"The table Next control was used {count} time(s) to load more rows "
                f"(row limit and page size apply)."
            ),
            status="PASSED",
        )
    )


def _install_action_log_hooks() -> None:
    """Record UI / browser / DB / click steps without changing action_log.py."""
    global _hooks_installed, _pagination_pending
    if _hooks_installed:
        return
    from Commons import action_log as al

    orig_ui = al.ui_action
    orig_browser = al.browser_log
    orig_click = al.click
    orig_query = al.memgraph_query
    orig_compare = al.compare_step
    orig_stat_ui = al.stat_bar_count_from_ui
    orig_stat_db = al.stat_bar_count_from_db
    orig_header = al.table_header_complete

    def ui_action(msg: str) -> None:
        _add_step(f"[UI] {msg}")
        orig_ui(msg)

    def browser_log(msg: str) -> None:
        _add_step(f"[Browser] {msg}")
        orig_browser(msg)

    def click(repo_key=None, xpath: str = "") -> None:
        global _pagination_pending
        if repo_key and _is_pagination_key(repo_key):
            _pagination_pending += 1
        elif repo_key:
            _add_step(f"Click: {repo_key}", detail=f"Object repository: {repo_key}")
        orig_click(repo_key, xpath)

    def memgraph_query(label: str, query: str) -> None:
        first = (query or "").strip().split("\n", 1)[0].strip()
        preview = first if len(first) <= 100 else first[:97] + "..."
        _add_step(f"[DB] {label}: {preview}", detail=(query or "").strip())
        orig_query(label, query)

    def compare_step(web_sheet: str, db_sheet: str) -> None:
        _add_step(f"Compare UI sheet {web_sheet} vs DB sheet {db_sheet}")
        orig_compare(web_sheet, db_sheet)

    def stat_bar_count_from_ui(name: str, value: str) -> None:
        _add_step(f"[UI] Stat bar {name}: {value}")
        orig_stat_ui(name, value)

    def stat_bar_count_from_db(name: str, value: str) -> None:
        _add_step(f"[DB] Expected stat bar {name}: {value}")
        orig_stat_db(name, value)

    def table_header_complete(app_key: str, hdr, raw_th_count: int) -> None:
        cols = " | ".join(str(h) for h in list(hdr)[:12])
        extra = " | …" if len(list(hdr)) > 12 else ""
        _add_step(
            f"[UI] Read table headers ({len(list(hdr))} columns)",
            detail=f"{cols}{extra}",
        )
        orig_header(app_key, hdr, raw_th_count)

    al.ui_action = ui_action
    al.browser_log = browser_log
    al.click = click
    al.memgraph_query = memgraph_query
    al.compare_step = compare_step
    al.stat_bar_count_from_ui = stat_bar_count_from_ui
    al.stat_bar_count_from_db = stat_bar_count_from_db
    al.table_header_complete = table_header_complete
    _hooks_installed = True


# ---------------------------------------------------------------------------
# Session / test records
# ---------------------------------------------------------------------------


@dataclass
class TestRecord:
    nodeid: str
    name: str
    outcome: str
    duration: float
    markers: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)
    execution_steps: List[ReportStep] = field(default_factory=list)
    check_steps: List[ReportStep] = field(default_factory=list)
    failure_message: str = ""
    log_text: str = ""
    screenshot_href: str = ""


@dataclass
class HtmlReportSession:
    enabled: bool
    started_at: float
    env: str = ""
    browser: str = ""
    headless: bool = True
    markexpr: str = ""
    argv_command: str = ""
    e2e_planned: int = 0
    records: List[TestRecord] = field(default_factory=list)


def _infer_slug_from_records(records: Sequence[TestRecord]) -> str:
    apps: List[str] = []
    suites: List[str] = []
    for rec in records:
        for m in rec.markers:
            ml = m.lower()
            if ml in _APP_MARKERS and ml.upper() not in apps:
                apps.append(ml.upper())
            if ml in _SUITE_MARKERS and ml not in suites:
                suites.append(ml)
    if apps and suites:
        return f"{apps[0]}_{suites[0]}"
    if apps:
        return apps[0]
    if suites:
        return suites[0]
    return "Run"


def _screenshot_path_for_item(nodeid: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid)[:150]
    return SCREENSHOT_DIR / f"{safe}.png"


def _collect_log_text(report: pytest.TestReport) -> str:
    chunks: List[str] = []
    if report.longreprtext:
        chunks.append(report.longreprtext.strip())
    for title, body in getattr(report, "sections", []) or []:
        if title in ("Captured stdout", "Captured stderr", "Captured log"):
            chunks.append(f"=== {title} ===\n{body}".strip())
    stdout = getattr(report, "capstdout", "") or ""
    stderr = getattr(report, "capstderr", "") or ""
    if stdout.strip():
        chunks.append("=== stdout ===\n" + stdout.strip())
    if stderr.strip():
        chunks.append("=== stderr ===\n" + stderr.strip())
    return "\n\n".join(chunks).strip()


def _parse_check_steps(check_blocks: List[str]) -> List[ReportStep]:
    steps: List[ReportStep] = []
    for block in check_blocks:
        for line in block.splitlines():
            text = line.strip()
            if not text:
                continue
            upper = text.upper()
            status = "FAILED" if "FAILED" in upper.split() else "PASSED"
            if "SKIPPED" in upper.split():
                status = "PASSED"
            steps.append(ReportStep(summary=text, status=status))
    return steps


def _effective_outcome(item: pytest.Item, report: pytest.TestReport) -> str:
    outcome = report.outcome
    try:
        apps = [v for v in item.funcargs.values() if isinstance(v, BaseApp)]
    except Exception:
        apps = []
    if outcome == "passed" and any(getattr(a, "failures", None) for a in apps):
        return "failed"
    return outcome


def _record_from_item(item: pytest.Item, report: pytest.TestReport) -> TestRecord:
    markers = sorted(m.name for m in item.iter_markers())
    checks: List[str] = []
    try:
        apps = [v for v in item.funcargs.values() if isinstance(v, BaseApp)]
    except Exception:
        apps = []
    for app in apps:
        if app.results:
            checks.append(app.report())
    for title, body in getattr(report, "sections", []) or []:
        if title == "Checks" and body.strip() and body.strip() not in checks:
            checks.append(body.strip())

    outcome = _effective_outcome(item, report)
    failure = ""
    if outcome == "failed":
        if report.longreprtext:
            failure = report.longreprtext
        else:
            parts = []
            for app in apps:
                parts.extend(getattr(app, "failures", []) or [])
            failure = "\n\n".join(parts)

    log_text = _collect_log_text(report) if outcome == "failed" else ""
    shot = _screenshot_path_for_item(item.nodeid)
    screenshot_href = f"screenshots/{shot.name}" if shot.is_file() else ""

    return TestRecord(
        nodeid=item.nodeid,
        name=item.name or item.nodeid,
        outcome=outcome,
        duration=getattr(report, "duration", 0.0) or 0.0,
        markers=markers,
        checks=checks,
        execution_steps=current_steps(),
        check_steps=_parse_check_steps(checks),
        failure_message=failure.strip(),
        log_text=log_text,
        screenshot_href=screenshot_href,
    )


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------


def _render_step_list(steps: Sequence[ReportStep], prefix: str, section_title: str) -> str:
    if not steps:
        return ""
    chunks: List[str] = [f'<h4>{html.escape(section_title)}</h4><div class="step-list">']
    for si, step in enumerate(steps):
        sid = f"{prefix}s{si}"
        status_class = "failed" if step.status == "FAILED" else "passed"
        if step.detail.strip():
            body = (
                f'<div id="{sid}" class="step-body">'
                f'<pre class="message">{html.escape(step.detail)}</pre></div>'
            )
        else:
            body = (
                f'<div id="{sid}" class="step-body">'
                f'<span class="muted">(summary only)</span></div>'
            )
        chunks.append(
            f"""
<div class="step" data-status="{html.escape(step.status)}">
  <div class="step-header" onclick="toggleStep('{sid}', event)" role="button" tabindex="0">
    <span class="step-num">{si + 1}</span>
    <span class="toggle-icon step-icon" id="icon-{sid}">▶</span>
    <span class="step-title">{html.escape(step.summary)}</span>
    <span class="{status_class} status">{html.escape(step.status)}</span>
  </div>
  {body}
</div>"""
        )
    chunks.append("</div>")
    return "".join(chunks)


def render_html(session: HtmlReportSession, *, generated: Optional[datetime] = None) -> str:
    generated = generated or datetime.now()
    records = session.records
    total = len(records)
    passed = sum(1 for r in records if r.outcome == "passed")
    failed = sum(1 for r in records if r.outcome == "failed")
    skipped = sum(1 for r in records if r.outcome == "skipped")
    elapsed_str = format_duration_hms(time.time() - session.started_at)
    slug = suite_slug_from_markexpr(session.markexpr)
    if slug == "Run":
        slug = _infer_slug_from_records(records)
    title = f"{slug} — Test Report"

    rows: List[str] = []
    for idx, rec in enumerate(records):
        status_class = rec.outcome if rec.outcome in ("passed", "failed", "skipped") else "incomplete"
        open_attr = ' class="test-body open"' if rec.outcome == "failed" else ' class="test-body"'
        chevron = "▼" if rec.outcome == "failed" else "▶"
        duration_s = format_duration_hms(rec.duration)
        marker_line = ", ".join(rec.markers) if rec.markers else "—"
        execution_html = _render_step_list(rec.execution_steps, f"t{idx}e", "Execution steps")
        checks_html = _render_step_list(rec.check_steps, f"t{idx}c", "Verification checks")

        log_html = ""
        if rec.log_text:
            log_html = (
                "<h4>Log / capture</h4>"
                "<pre class=\"log message\">" + html.escape(rec.log_text) + "</pre>"
            )
        fail_html = ""
        if rec.failure_message and rec.failure_message not in (rec.log_text or ""):
            fail_html = (
                "<h4>Failure</h4>"
                "<pre class=\"log failed message\">" + html.escape(rec.failure_message) + "</pre>"
            )
        shot_html = ""
        if rec.screenshot_href:
            esc = html.escape(rec.screenshot_href)
            shot_html = (
                f'<h4>Screenshot</h4>'
                f'<a href="{esc}"><img class="screenshot" src="{esc}" alt="screenshot"/></a>'
            )

        rows.append(
            f"""
<div class="test" data-outcome="{html.escape(rec.outcome)}">
  <div class="test-header" onclick="toggleTest('t{idx}')" role="button" tabindex="0">
    <span class="toggle-icon" id="icon-t{idx}">{chevron}</span>
    <span class="test-name">{html.escape(rec.name)}</span>
    <span class="test-duration">{html.escape(duration_s)}</span>
    <span class="{status_class} status">{html.escape(rec.outcome.upper())}</span>
  </div>
  <div id="t{idx}"{open_attr}>
    <div class="meta">Markers: {html.escape(marker_line)}</div>
    <div class="meta">Node: {html.escape(rec.nodeid)}</div>
    {execution_html}
    {checks_html}
    {fail_html}
    {log_html}
    {shot_html}
  </div>
</div>"""
        )

    host = socket.gethostname()
    os_name = platform.platform()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>
body {{ font-family: Helvetica, Arial, sans-serif; font-size: 0.85em; color: #111; margin: 0; padding: 12px; background: #fff; }}
#header {{ margin-bottom: 12px; overflow: hidden; }}
h1 {{ margin: 0 0 4px 0; font-size: 1.4em; }}
#generated {{ float: right; text-align: right; color: #444; font-size: 0.9em; }}
.passed {{ color: #009900 !important; font-weight: bold; }}
.failed {{ color: #c00 !important; font-weight: bold; }}
.skipped {{ color: #808080 !important; }}
table.stats {{ border-collapse: collapse; margin: 12px 0; width: 100%; max-width: 720px; }}
table.stats th, table.stats td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
table.stats th {{ background: #eee; }}
.env-table td:first-child {{ font-weight: bold; width: 140px; }}
.test {{ border: 1px solid #ddd; margin: 8px 0; border-radius: 4px; }}
.test-header {{ display: flex; align-items: center; gap: 10px; padding: 8px 10px; background: #f7f7f7; cursor: pointer; user-select: none; }}
.test-header:hover {{ background: #eee; }}
.toggle-icon {{ width: 1em; color: #555; }}
.test-name {{ flex: 1; font-weight: bold; word-break: break-word; }}
.test-duration {{ color: #666; white-space: nowrap; }}
.status {{ min-width: 5em; text-align: right; }}
.test-body {{ display: none; padding: 10px 14px; border-top: 1px solid #ddd; }}
.test-body.open {{ display: block; }}
.meta {{ color: #555; font-size: 0.9em; margin-bottom: 6px; }}
h4 {{ margin: 12px 0 4px 0; font-size: 1em; color: #333; }}
.step-list {{ margin: 6px 0 12px 0; border-left: 3px solid #ddd; padding-left: 4px; }}
.step {{ border: 1px solid #e4e4e4; margin: 4px 0; border-radius: 3px; background: #fff; }}
.step-header {{ display: flex; align-items: center; gap: 8px; padding: 6px 8px; cursor: pointer; font-size: 0.95em; }}
.step-header:hover {{ background: #f3f3f3; }}
.step-num {{ color: #888; min-width: 1.5em; text-align: right; font-weight: bold; }}
.step-title {{ flex: 1; word-break: break-word; }}
.step-body {{ display: none; padding: 6px 10px 8px 2.5em; border-top: 1px solid #eee; background: #fafafa; }}
.step-body.open {{ display: block; }}
.muted {{ color: #888; font-size: 0.9em; }}
pre.log {{ white-space: pre-wrap; word-wrap: break-word; background: #fafafa; border: 1px solid #e0e0e0; padding: 8px; font-size: 0.92em; }}
pre.log.failed {{ border-color: #f5c2c2; background: #fff5f5; }}
.message {{ font-family: Consolas, Monaco, monospace; }}
img.screenshot {{ max-width: 100%; border: 1px solid #99c; margin-top: 6px; }}
.toolbar {{ margin: 10px 0; }}
.toolbar button {{ margin-right: 8px; padding: 4px 10px; cursor: pointer; }}
a {{ color: #06c; }}
</style>
</head>
<body>
<div id="header">
  <div id="generated">Generated<br/>{html.escape(generated.strftime("%Y-%m-%d %H:%M:%S"))}</div>
  <h1>{html.escape(title)}</h1>
  <div>Command: <code>{html.escape(session.argv_command or "pytest")}</code></div>
</div>

<table class="stats">
  <tr><th>Total</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Elapsed</th></tr>
  <tr>
    <td>{total}</td>
    <td class="passed">{passed}</td>
    <td class="failed">{failed}</td>
    <td class="skipped">{skipped}</td>
    <td>{elapsed_str}</td>
  </tr>
</table>

<table class="stats env-table">
  <tr><td>Environment</td><td>{html.escape(session.env or "—")}</td></tr>
  <tr><td>Browser</td><td>{html.escape(session.browser or "—")} (headless={session.headless})</td></tr>
  <tr><td>Host</td><td>{html.escape(host)}</td></tr>
  <tr><td>OS</td><td>{html.escape(os_name)}</td></tr>
</table>

<div class="toolbar">
  <button type="button" onclick="expandAll(true)">Expand all tests</button>
  <button type="button" onclick="expandAll(false)">Collapse all tests</button>
  <button type="button" onclick="expandAllSteps(true)">Expand all steps</button>
  <button type="button" onclick="expandAllSteps(false)">Collapse all steps</button>
  <button type="button" onclick="expandFailed()">Expand failed only</button>
</div>

<div id="tests">
{"".join(rows) if rows else "<p>No test results recorded.</p>"}
</div>

<script>
function toggleTest(id) {{
  var el = document.getElementById(id);
  var icon = document.getElementById('icon-' + id);
  if (!el) return;
  el.classList.toggle('open');
  if (icon) icon.textContent = el.classList.contains('open') ? '▼' : '▶';
}}
function toggleStep(id, ev) {{
  if (ev) ev.stopPropagation();
  var el = document.getElementById(id);
  var icon = document.getElementById('icon-' + id);
  if (!el) return;
  el.classList.toggle('open');
  if (icon) icon.textContent = el.classList.contains('open') ? '▼' : '▶';
}}
function expandAll(open) {{
  document.querySelectorAll('.test-body').forEach(function(el) {{
    if (open) el.classList.add('open'); else el.classList.remove('open');
  }});
  document.querySelectorAll('.test-header .toggle-icon').forEach(function(icon) {{
    icon.textContent = open ? '▼' : '▶';
  }});
}}
function expandAllSteps(open) {{
  document.querySelectorAll('.step-body').forEach(function(el) {{
    if (open) el.classList.add('open'); else el.classList.remove('open');
  }});
  document.querySelectorAll('.step-icon').forEach(function(icon) {{
    icon.textContent = open ? '▼' : '▶';
  }});
}}
function expandFailed() {{
  expandAll(false);
  expandAllSteps(false);
  document.querySelectorAll('.test[data-outcome="failed"] .test-body').forEach(function(el) {{
    el.classList.add('open');
  }});
  document.querySelectorAll('.test[data-outcome="failed"] .test-header .toggle-icon').forEach(function(icon) {{
    icon.textContent = '▼';
  }});
  document.querySelectorAll('.step[data-status="FAILED"] .step-body').forEach(function(el) {{
    el.classList.add('open');
  }});
  document.querySelectorAll('.step[data-status="FAILED"] .step-icon').forEach(function(icon) {{
    icon.textContent = '▼';
  }});
}}
document.querySelectorAll('.test-header, .step-header').forEach(function(h) {{
  h.addEventListener('keydown', function(e) {{
    if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); h.click(); }}
  }});
}});
</script>
</body>
</html>"""


def _write_report(session: HtmlReportSession) -> Optional[Path]:
    if not session.records:
        return None
    slug = suite_slug_from_markexpr(session.markexpr)
    if slug == "Run":
        slug = _infer_slug_from_records(session.records)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{slug}_{stamp}.html"
    text = render_html(session)
    path.write_text(text, encoding="utf-8")
    (REPORTS_DIR / "latest.html").write_text(text, encoding="utf-8")
    return path


def _xdist_parallel(config: pytest.Config) -> bool:
    try:
        n = config.getoption("numprocesses", default=None)
        return n is not None and str(n) not in ("0", "no")
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# pytest hooks
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    global _active_config
    _active_config = config
    from Commons.settings import _load_local_env

    _load_local_env()
    enabled = html_report_enabled()
    if enabled:
        _install_action_log_hooks()
    try:
        from Commons.settings import resolve_test_env

        env = resolve_test_env(config.getoption("--env"))
    except Exception:
        env = os.environ.get("ENV", "qa")
    browser = config.getoption("--browser", default=None) or os.environ.get("BROWSER", "chromium")
    if config.getoption("--headed", default=False):
        headless = False
    else:
        headless = str(os.environ.get("HEADLESS", "true")).strip().lower() not in ("0", "false", "no")
    inv = getattr(config, "invocation_params", None)
    argv = " ".join(inv.args) if inv else "pytest"
    config.stash[_stash_key] = HtmlReportSession(
        enabled=enabled,
        started_at=time.time(),
        env=env,
        browser=browser,
        headless=headless,
        markexpr=getattr(config.option, "markexpr", "") or "",
        argv_command=argv,
    )
    config.stash[_item_map_key] = {}


def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]) -> None:
    session = config.stash.get(_stash_key, None)
    if session is None:
        return
    session.e2e_planned = sum(1 for item in items if item.get_closest_marker("unit") is None)
    markexpr = (getattr(config.option, "markexpr", "") or "").strip()
    if markexpr:
        session.markexpr = markexpr


@pytest.hookimpl
def pytest_runtest_setup(item: pytest.Item) -> None:
    session: Optional[HtmlReportSession] = item.config.stash.get(_stash_key, None)
    if session is None or not session.enabled:
        return
    if _xdist_parallel(item.config) or hasattr(item.config, "workerinput"):
        return
    if item.get_closest_marker("unit") is None:
        clear_steps()
    item.config.stash[_item_map_key][item.nodeid] = item


@pytest.hookimpl
def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when != "call":
        return
    config = _active_config
    if config is None:
        return
    session: Optional[HtmlReportSession] = config.stash.get(_stash_key, None)
    if session is None or not session.enabled:
        return
    if _xdist_parallel(config) or hasattr(config, "workerinput"):
        return
    item = config.stash.get(_item_map_key, {}).pop(report.nodeid, None)
    if item is None or item.get_closest_marker("unit") is not None:
        return
    session.records.append(_record_from_item(item, report))


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    data = session.config.stash.get(_stash_key, None)
    if data is None:
        return
    if _xdist_parallel(session.config) or hasattr(session.config, "workerinput"):
        if data.enabled:
            print(
                "\nHTML report: skipped (pytest-xdist -n not supported yet; run without -n)",
                flush=True,
            )
        return
    if not data.enabled:
        if data.e2e_planned > 0:
            print(
                "\nHTML report: off (set HTML_REPORT=true in commons-automation/.env)",
                flush=True,
            )
        return
    path = _write_report(data)
    if path is not None:
        print(f"\nHTML report: {path}", flush=True)
        print(f"HTML report (latest): {REPORTS_DIR / 'latest.html'}", flush=True)
    elif data.e2e_planned > 0:
        print("\nHTML report: enabled but no results captured", flush=True)
    else:
        print("\nHTML report: no E2E tests in this run (-m unit only or empty collection)", flush=True)
