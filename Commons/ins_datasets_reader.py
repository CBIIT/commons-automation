"""Read INS DataSets explore results (card layout, not MUI table)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, List

from Commons import action_log
from Commons.db_source import Table

if TYPE_CHECKING:
    from Commons.browser_actions import Ui
    from Commons.object_repository import ObjectRepository

_HEADER = ["Title", "Source ID", "Primary Disease", "Sample Count"]

_CARD_ROWS_JS = """
() => {
  const out = [];
  const seen = new Set();
  for (const sampleEl of document.querySelectorAll('.textSpan.sampleCountHighlight')) {
    const card = sampleEl.closest('.container');
    if (!card || seen.has(card)) continue;
    seen.add(card);
    const title = (card.querySelector('a[href^="#/dataset/"]')?.innerText || '').replace(/\\s+/g, ' ').trim();
    const sourceEl = card.querySelector('a[href^="https://cedcd"], a[href^="https://www.ncbi.nlm"]');
    const sourceId = (sourceEl?.innerText || '').replace(/\\s+/g, ' ').trim();
    const primary = (card.querySelector('.itemSpan')?.innerText || '').replace(/\\s+/g, ' ').trim();
    const sample = (sampleEl?.innerText || '').replace(/\\s+/g, ' ').trim();
    if (title || sourceId) out.push([title, sourceId, primary, sample]);
  }
  return out;
}
"""


def _set_max_rows_per_page(ui: "Ui", repo: "ObjectRepository") -> None:
    dd = repo.xpath("DataSets/RowsPerPage-Dd")
    pick = repo.xpath("DataSets/RowPerPaDd-Value")
    if not ui.is_visible(dd):
        return
    ui.click(dd, repo_key="DataSets/RowsPerPage-Dd")
    ui.wait_idle(500)
    if ui.is_visible(pick):
        ui.click(pick, repo_key="DataSets/RowPerPaDd-Value")
        ui.wait_idle(1500)


def _next_disabled(ui: "Ui", next_xp: str) -> bool:
    if not ui.is_visible(next_xp):
        return True
    cls = ui.loc(next_xp).first.get_attribute("class") or ""
    return "disabled" in cls


def read_ins_datasets_ui(ui: "Ui", repo: "ObjectRepository", *, max_pages: int = 50) -> Table:
    """Scrape dataset cards across bootstrap-style pages (Katalon verifyUiAgainstTsvForInsDatasetsTab)."""
    _set_max_rows_per_page(ui, repo)
    next_xp = repo.xpath("DataSets/Next-Btn")
    rows: List[List[str]] = []
    for page in range(1, max_pages + 1):
        chunk = ui.page.evaluate(_CARD_ROWS_JS)
        if chunk:
            rows.extend(chunk)
        action_log.say(f"INS DataSets UI page {page}: {len(chunk)} card(s)")
        if _next_disabled(ui, next_xp):
            break
        ui.scroll_into_view(next_xp)
        ui.click(next_xp, repo_key="DataSets/Next-Btn")
        ui.wait_idle(1000)
        time.sleep(0.5)
    return Table(header=list(_HEADER), rows=rows)
