"""
App-facing browser API: logging, stat-bar stability, facet scroll, table helpers.

XPath clicks and reads delegate to Commons.utils (Playwright primitives).
"""
import time
from typing import List, Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from Commons import action_log
from Commons import utils as pw

_FIND_FACET_SCROLLER_JS = """
(header) => {
  const h = header.closest("[role='button']") || header;
  let root = h.closest(".MuiAccordion-root");
  if (!root) {
    let p = h.parentElement;
    for (let i = 0; i < 10 && p; i++) {
      if (((p.className || '') + '').includes('MuiAccordion')) { root = p; break; }
      p = p.parentElement;
    }
  }
  const scrollable = (el) => {
    const oy = getComputedStyle(el).overflowY;
    return (oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight + 1;
  };
  if (root) {
    const region = root.querySelector('.MuiCollapse-root') || root;
    for (const el of region.querySelectorAll('*')) if (scrollable(el)) return el;
  }
  const hr = h.getBoundingClientRect();
  let best = null, bestOverflow = 0;
  for (const el of document.querySelectorAll('*')) {
    if (!scrollable(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.top < hr.bottom - 8 || r.left > 420 || r.width < 100 || r.height < 50) continue;
    const o = el.scrollHeight - el.clientHeight;
    if (o > bestOverflow) { bestOverflow = o; best = el; }
  }
  return best;
}
"""

_READ_ROWS_JS = """
(tbody, o) => {
  return Array.from(tbody.querySelectorAll(':scope > tr')).map(tr => {
    const cells = Array.from(tr.children);
    const out = [];
    for (let k = 0; k < o.count; k++) {
      const c = cells[o.start + k];
      if (!c) { out.push(''); continue; }
      let t;
      if (o.firstChild) { const f = c.firstElementChild; t = f ? f.innerText : c.innerText; }
      else { t = c.innerText; }
      out.push(t == null ? '' : t);
    }
    return out;
  });
}
"""


class Ui:
    """Thin wrapper around a Playwright Page (XPath + action logging)."""

    def __init__(self, page: Page, timeout_ms: int = 30000):
        self.page = page
        self.timeout_ms = timeout_ms

    def loc(self, xpath: str) -> Locator:
        return pw.xpath_locator(self.page, xpath)

    def visible(self, xpath: str) -> Locator:
        return pw.visible_xpath_locator(self.page, xpath)

    def is_visible(self, xpath: str) -> bool:
        return pw.is_visible(self.page, xpath)

    def is_present(self, xpath: str) -> bool:
        return pw.is_present(self.page, xpath)

    def wait_idle(self, timeout_ms: int = 8000):
        try:
            pw.wait_load_state(self.page, "networkidle", timeout_ms=timeout_ms)
        except PlaywrightTimeout:
            pass

    def wait_visible(self, xpath: str, timeout_ms: Optional[int] = None) -> Locator:
        return pw.wait_visible(self.page, xpath, timeout_ms=timeout_ms or self.timeout_ms)

    def click(self, xpath: str, timeout_ms: int = 10000, prefer_visible: bool = True, repo_key: str = None):
        action_log.click(repo_key, xpath)
        pw.click_element(
            self.page,
            xpath,
            prefer_visible=prefer_visible,
            attached_timeout_ms=timeout_ms,
        )

    def js_click(self, xpath: str, timeout_ms: int = 10000, repo_key: str = None):
        action_log.click(repo_key, xpath)
        pw.js_click(self.page, xpath, attached_timeout_ms=timeout_ms)

    def scroll_into_view(self, xpath: str):
        pw.scroll_into_view(self.page, xpath, timeout_ms=self.timeout_ms)

    def fill(self, xpath: str, text: str, timeout_ms: int = 10000, repo_key: str = None):
        action_log.fill(xpath, text, repo_key)
        pw.fill(self.page, xpath, text, timeout_ms=timeout_ms)

    def text(self, xpath: str) -> str:
        return pw.text(self.page, xpath, timeout_ms=self.timeout_ms)

    def html(self, xpath: str) -> str:
        return pw.html(self.page, xpath, timeout_ms=self.timeout_ms)

    def attr(self, xpath: str, name: str) -> Optional[str]:
        return pw.attribute(self.page, xpath, name, timeout_ms=self.timeout_ms)

    def stable_text(self, xpath: str, use_html: bool = False, settle_s: float = 1.0,
                    timeout_s: float = 20.0, label: str = None) -> str:
        target = pw.locator(self.page, xpath)
        target.wait_for(state="attached", timeout=int(timeout_s * 1000))
        read = target.inner_html if use_html else target.inner_text
        deadline = time.time() + timeout_s
        last, since = None, time.time()
        while time.time() < deadline:
            try:
                value = (read() or "").strip()
            except PlaywrightError:
                value = ""
            if value and value == last:
                if time.time() - since >= settle_s:
                    return value
            else:
                last, since = value, time.time()
            time.sleep(0.15)
        out = last or ""
        if label:
            action_log.say(f"read ({label}) xpath: {xpath} -> {out!r}")
        return out

    def stable_texts(self, items, settle_s: float = 1.0, timeout_s: float = 20.0) -> list:
        targets = [(pw.locator(self.page, xp), use_html) for xp, use_html in items]
        for t, _ in targets:
            t.wait_for(state="attached", timeout=int(timeout_s * 1000))
        deadline = time.time() + timeout_s
        last, since = None, time.time()
        while time.time() < deadline:
            try:
                values = [((t.inner_html() if h else t.inner_text()) or "").strip() for t, h in targets]
            except PlaywrightError:
                values = [""] * len(targets)
            if all(values) and values == last:
                if time.time() - since >= settle_s:
                    return values
            else:
                last, since = values, time.time()
            time.sleep(0.15)
        out = last or [""] * len(targets)
        for (xp, _), val in zip(items, out):
            action_log.say(f"read stat xpath: {xp} -> {val!r}")
        return out

    def scroll_facet_until_visible(self, header_xpath: str, target_xpath: str, timeout_s: float = 10.0) -> bool:
        if self.is_present(target_xpath):
            return True
        header = pw.locator(self.page, header_xpath)
        header.wait_for(state="attached", timeout=self.timeout_ms)
        handle = header.evaluate_handle(_FIND_FACET_SCROLLER_JS)
        scroller = handle.as_element()
        if scroller is None:
            return self.is_present(target_xpath)
        end = time.time() + timeout_s
        stuck = 0
        while time.time() < end:
            if self.is_present(target_xpath):
                return True
            before = scroller.evaluate("e => e.scrollTop")
            scroller.evaluate("e => { e.scrollTop = e.scrollTop + e.clientHeight * 3; }")
            time.sleep(0.25)
            after = scroller.evaluate("e => e.scrollTop")
            if after == before:
                stuck += 1
                scroller.evaluate("e => { e.scrollTop = e.scrollHeight; }")
                time.sleep(0.4)
                if stuck >= 4:
                    break
            else:
                stuck = 0
        return self.is_present(target_xpath)

    def header_texts(self, header_xpath: str) -> List[str]:
        cols = self.loc(header_xpath + "//th").evaluate_all("els => els.map(e => e.innerText)")
        action_log.table_header_columns([c.strip() for c in cols])
        return cols

    def read_body(self, body_xpath: str, start: int, count: int, first_child: bool = False) -> List[List[str]]:
        rows = self.loc(body_xpath).first.evaluate(
            _READ_ROWS_JS, {"start": start, "count": count, "firstChild": first_child})
        action_log.table_page_size(len(rows))
        for i, cells in enumerate(rows, start=1):
            action_log.table_row_cells(i, cells)
            action_log.table_body_line("||".join(str(c) for c in cells) + "||")
        return rows
