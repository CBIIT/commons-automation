"""
pytest wiring: browser, environment and one ready-to-use fixture per application.

Katalon equivalent: the Profile chosen at run time + the browser Katalon opened for you.

    pytest --env qa                    # which environment (qa | stage | prod), default ENV or qa
    pytest --headed                    # watch the browser (or HEADLESS=false / HEADED=true in .env)
    pytest --browser firefox           # chromium (default) | firefox | webkit (or BROWSER=firefox)
    pytest -m "c3dc and smoke"         # a suite
    pytest Testcases/c3dc/studies/phs000466/test_TC01_C3DC_phs000466_SexAtBirth_Male.py   # one case
"""
import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from Commons.apps import APPS, BaseApp
from Commons.memgraph_source import LazySource
from Commons.object_repository import ObjectRepository
from Commons import action_log
from Commons.settings import (
    ROOT,
    get_app_settings,
    get_browser_settings,
    load_config,
    resolve_test_env,
)

SCREENSHOT_DIR = ROOT / "Reports" / "screenshots"


def pytest_addoption(parser):
    g = parser.getgroup("commons-automation")
    g.addoption("--env", default=None, help="Environment: qa | stage | prod (default: ENV or qa)")
    g.addoption("--headed", action="store_true", default=False, help="Show the browser window")
    g.addoption("--browser", default=None, help="chromium | firefox | webkit")
    g.addoption("--slowmo", type=int, default=0, help="Slow every browser action down by N ms")
    g.addoption(
        "--trace-actions",
        action="store_true",
        default=False,
        help="Print every action, xpath, UI/DB row to the console (Katalon-style; or set COMMONS_VERBOSE=1)",
    )


def pytest_configure(config):
    action_log.set_pytest_config(config)
    if config.getoption("--trace-actions", default=False):
        action_log.set_enabled(True)


@pytest.fixture(scope="session")
def env(request):
    return resolve_test_env(request.config.getoption("--env"))


@pytest.fixture(scope="session")
def browser_settings(request):
    headless = False if request.config.getoption("--headed") else None
    return get_browser_settings(
        load_config(),
        name=request.config.getoption("--browser"),
        headless=headless,
    )


@pytest.fixture(scope="session")
def browser(browser_settings, request):
    with sync_playwright() as p:
        launcher = getattr(p, browser_settings.name)
        slowmo = request.config.getoption("--slowmo") or int(os.environ.get("SLOWMO", "0") or 0)
        b = launcher.launch(headless=browser_settings.headless, slow_mo=slowmo)
        action_log.browser_log(
            f"Opened {browser_settings.name} (headless={browser_settings.headless}, slow_mo={slowmo} ms)"
        )
        yield b
        action_log.browser_log("Closing browser (session end)")
        b.close()


@pytest.fixture
def page(browser, browser_settings):
    context = browser.new_context(viewport=browser_settings.viewport)
    context.set_default_timeout(browser_settings.timeout_ms)
    pg = context.new_page()
    action_log.browser_log("Opened browser context for test")
    yield pg
    action_log.browser_log("Closing browser context (END of TEST)")
    context.close()


@pytest.fixture(scope="session")
def _repos():
    cache = {}

    def get(app_name):
        if app_name not in cache:
            cache[app_name] = ObjectRepository(app_name)
        return cache[app_name]
    return get


def _make_app(app_name, page, env, browser_settings, _repos):
    settings = get_app_settings(app_name, env)
    source = LazySource(settings)
    app = APPS[app_name](page, settings, _repos(app_name), source, browser_settings.timeout_ms)
    app.open()
    return app, source


@pytest.fixture
def c3dc(page, env, browser_settings, _repos):
    """C3DC, already opened at the environment's URL."""
    app, source = _make_app("C3DC", page, env, browser_settings, _repos)
    yield app
    source.close()


@pytest.fixture
def gc(page, env, browser_settings, _repos):
    """GC (General Commons), already opened at the environment's URL."""
    app, source = _make_app("GC", page, env, browser_settings, _repos)
    yield app
    source.close()


@pytest.fixture
def ctdc(page, env, browser_settings, _repos):
    """CTDC (Clinical Trials Data Commons), already opened at the environment's URL."""
    app, source = _make_app("CTDC", page, env, browser_settings, _repos)
    yield app
    source.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Fail a test whose tab/stat-bar checks failed (they are collected, not raised one by one),
    print a per-check summary, and save a screenshot when a test fails."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return
    apps = [v for v in item.funcargs.values() if isinstance(v, BaseApp)]
    for app in apps:
        if app.results:
            rep.sections.append(("Checks", app.report()))
        if rep.passed and app.failures:
            rep.outcome = "failed"
            rep.longrepr = "\n\n".join(app.failures)
    if rep.failed:
        pg = item.funcargs.get("page")
        if pg is not None:
            try:
                SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
                name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.nodeid)[:150]
                pg.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=False)
            except Exception:
                pass
