"""
Playwright UI helpers (sync API): XPath locators, click, read text, waits.

Uses the browser context default timeout from conftest unless a call passes timeout_ms.
"""
from typing import Literal, Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

LoadState = Literal["load", "domcontentloaded", "networkidle"]


# ---------------------------------------------------------------------------
# Locators (XPath → Playwright Locator)
# ---------------------------------------------------------------------------


def xpath_locator(page: Page, xpath: str) -> Locator:
    """All DOM matches for this XPath (use .first / .count / .evaluate_all)."""
    return page.locator(f"xpath={xpath}")


def visible_xpath_locator(page: Page, xpath: str) -> Locator:
    """All currently visible matches (ignores hidden copies in other tabs)."""
    return page.locator(f"xpath={xpath} >> visible=true")


def locator(page: Page, xpath: str) -> Locator:
    """First DOM match for this XPath."""
    return xpath_locator(page, xpath).first


def visible_locator(page: Page, xpath: str) -> Locator:
    """First visible match."""
    return visible_xpath_locator(page, xpath).first


# ---------------------------------------------------------------------------
# Presence and visibility
# ---------------------------------------------------------------------------


def is_visible(page: Page, xpath: str) -> bool:
    try:
        return visible_xpath_locator(page, xpath).count() > 0
    except PlaywrightError:
        return False


def is_present(page: Page, xpath: str) -> bool:
    return xpath_locator(page, xpath).count() > 0


# ---------------------------------------------------------------------------
# Clicks and pointer actions
# ---------------------------------------------------------------------------


def click_element(
    page: Page,
    xpath: str,
    *,
    prefer_visible: bool = True,
    attached_timeout_ms: int = 10000,
    click_timeout_ms: int = 4000,
    scroll_timeout_ms: int = 3000,
) -> None:
    """Scroll into view, click; JS click if Playwright reports intercept or timeout."""
    target = (
        visible_locator(page, xpath)
        if prefer_visible and is_visible(page, xpath)
        else locator(page, xpath)
    )
    target.wait_for(state="attached", timeout=attached_timeout_ms)
    try:
        target.scroll_into_view_if_needed(timeout=scroll_timeout_ms)
        target.click(timeout=click_timeout_ms)
    except (PlaywrightTimeout, PlaywrightError):
        js_click(page, xpath)


def js_click(page: Page, xpath: str, *, attached_timeout_ms: int = 10000) -> None:
    target = locator(page, xpath)
    target.wait_for(state="attached", timeout=attached_timeout_ms)
    target.evaluate("el => { el.scrollIntoView({block: 'center'}); el.click(); }")


def double_click(page: Page, xpath: str) -> None:
    visible_locator(page, xpath).dblclick()


def hover(page: Page, xpath: str) -> None:
    visible_locator(page, xpath).hover()


# ---------------------------------------------------------------------------
# Form input (type, check, select)
# ---------------------------------------------------------------------------


def fill(page: Page, xpath: str, text: str, *, timeout_ms: int = 10000) -> None:
    target = locator(page, xpath)
    target.wait_for(state="visible", timeout=timeout_ms)
    target.click()
    target.fill(text)


def clear_input(page: Page, xpath: str) -> None:
    locator(page, xpath).clear()


def press_sequentially(page: Page, xpath: str, text: str, *, delay: float = 0) -> None:
    locator(page, xpath).press_sequentially(text, delay=delay)


def press_key(page: Page, xpath: str, key: str) -> None:
    locator(page, xpath).press(key)


def check(page: Page, xpath: str) -> None:
    locator(page, xpath).check()


def uncheck(page: Page, xpath: str) -> None:
    locator(page, xpath).uncheck()


def select_option(page: Page, xpath: str, value: str) -> None:
    locator(page, xpath).select_option(value)


# ---------------------------------------------------------------------------
# Read element state
# ---------------------------------------------------------------------------


def text(page: Page, xpath: str, *, timeout_ms: Optional[int] = None) -> str:
    kwargs = {} if timeout_ms is None else {"timeout": timeout_ms}
    return locator(page, xpath).inner_text(**kwargs).strip()


def html(page: Page, xpath: str, *, timeout_ms: Optional[int] = None) -> str:
    kwargs = {} if timeout_ms is None else {"timeout": timeout_ms}
    return locator(page, xpath).inner_html(**kwargs)


def attribute(page: Page, xpath: str, name: str, *, timeout_ms: Optional[int] = None) -> Optional[str]:
    kwargs = {} if timeout_ms is None else {"timeout": timeout_ms}
    return locator(page, xpath).get_attribute(name, **kwargs)


def input_value(page: Page, xpath: str) -> str:
    return locator(page, xpath).input_value()


def count(page: Page, xpath: str) -> int:
    return xpath_locator(page, xpath).count()


def is_enabled(page: Page, xpath: str) -> bool:
    return locator(page, xpath).is_enabled()


def is_checked(page: Page, xpath: str) -> bool:
    return locator(page, xpath).is_checked()


# ---------------------------------------------------------------------------
# Waits and scroll
# ---------------------------------------------------------------------------


def wait_visible(page: Page, xpath: str, *, timeout_ms: int = 30000) -> Locator:
    target = visible_locator(page, xpath)
    target.wait_for(state="visible", timeout=timeout_ms)
    return target


def wait_hidden(page: Page, xpath: str) -> None:
    locator(page, xpath).wait_for(state="hidden")


def wait_attached(page: Page, xpath: str) -> Locator:
    loc = locator(page, xpath)
    loc.wait_for(state="attached")
    return loc


def wait_detached(page: Page, xpath: str) -> None:
    locator(page, xpath).wait_for(state="detached")


def wait_load_state(page: Page, state: LoadState = "networkidle", *, timeout_ms: Optional[int] = None) -> None:
    kwargs = {"state": state}
    if timeout_ms is not None:
        kwargs["timeout"] = timeout_ms
    page.wait_for_load_state(**kwargs)


def scroll_into_view(page: Page, xpath: str, *, timeout_ms: int = 30000) -> None:
    locator(page, xpath).scroll_into_view_if_needed(timeout=timeout_ms)
