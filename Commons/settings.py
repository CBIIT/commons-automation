"""
Loads test config: URLs and DB hosts from Config/environments.yaml; passwords from .env only.

Tests usually call get_app_settings(app, env) (pytest --env or ENV, default qa).
See "Public settings API" below for get_browser_settings, get_app_url, and get_db_settings.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "Config" / "environments.yaml"
OBJECT_REPO_ROOT = ROOT / "ObjectRepository"
INPUTFILES_ROOT = Path(
    os.environ.get("INPUTFILES_ROOT")
    or os.environ.get("TESTDATA_ROOT")  # legacy env name
    or ROOT / "InputFiles"
)
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", ROOT / "OutputFiles"))

DEFAULT_ENV = "qa"
_LOCAL_ENV = ROOT / ".env"


def _load_local_env() -> None:
    """Optional gitignored `.env` in commons-automation/ (local dev). Does not override existing env vars."""
    if not _LOCAL_ENV.is_file():
        return
    for line in _LOCAL_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()


# ---------------------------------------------------------------------------
# Settings dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BrowserSettings:
    name: str = "chromium"
    headless: bool = True
    viewport: dict = field(default_factory=lambda: {"width": 1920, "height": 1080})
    timeout_ms: int = 30000


@dataclass
class DbSettings:
    """Bolt connection for expected data from input workbooks (Memgraph or Neo4j)."""

    expected_source: str = "memgraph"
    endpoint: str = ""
    username: str = ""
    password: str = ""  # env only; never from YAML
    bolt_env: str = ""  # YAML/env block for bolt; may differ from UI env (ICDC NEO4J_ENV)


@dataclass
class AppSettings:
    """UI URL + bolt DB settings for one app in one test environment."""

    app: str
    env: str
    url: str
    db: DbSettings
    tab_row_limit: int = 100  # UI rows + DB tab Cypher LIMIT (Config/tab_setting.yaml)
    pagination_max_pages: int = 50  # UI pagination safety cap (same file)
    tab_execution: dict = field(default_factory=dict)  # tab name -> enabled (verify_tab)

    @property
    def expected_source(self) -> str:
        return self.db.expected_source

    @property
    def db_env(self) -> str:
        return self.db.bolt_env or self.env

    @property
    def memgraph_endpoint(self) -> str:
        return self.db.endpoint

    @property
    def memgraph_username(self) -> str:
        return self.db.username

    @property
    def memgraph_password(self) -> str:
        return self.db.password


# ---------------------------------------------------------------------------
# Bolt env var names (document in .env; used in db_source error messages)
# ---------------------------------------------------------------------------


def memgraph_password_env_keys(app: str, env: str) -> tuple[str, str]:
    """Env var names to set Memgraph password for this app (per-cluster; no shared password)."""
    app_u, env_u = app.upper(), env.upper()
    return (
        f"MEMGRAPH_PASSWORD_{app_u}_{env_u}",
        f"MEMGRAPH_PASSWORD_{app_u}",
    )


def neo4j_password_env_keys(app: str, env: str) -> tuple[str, str]:
    app_u, env_u = app.upper(), env.upper()
    return (
        f"NEO4J_PASSWORD_{app_u}_{env_u}",
        f"NEO4J_PASSWORD_{app_u}",
    )


# ---------------------------------------------------------------------------
# Bolt connection env resolution (internal; used by get_db_settings)
# ---------------------------------------------------------------------------


def _neo4j_env(app: str, env: str, field: str, yaml_value: str = "") -> str:
    """Resolve Neo4j bolt endpoint / username (env overrides, then YAML).

    Falls back to MEMGRAPH_* env names so existing ICDC `.env` entries keep working.
    Passwords use `_expected_db_password` (NEO4J_PASSWORD_* first).
    """
    app_u, env_u = app.upper(), env.upper()
    field_u = field.upper()
    keys = [
        f"NEO4J_{field_u}_{app_u}_{env_u}",
        f"NEO4J_{field_u}_{app_u}",
        f"MEMGRAPH_{field_u}_{app_u}_{env_u}",
        f"MEMGRAPH_{field_u}_{app_u}",
    ]
    if field_u != "PASSWORD":
        keys.extend([f"NEO4J_{field_u}", f"MEMGRAPH_{field_u}"])
    for key in keys:
        val = os.environ.get(key)
        if val:
            return val
    return yaml_value or ""


def neo4j_bolt_env(app: str, ui_env: str) -> str:
    """Which env block to use for Neo4j bolt (ICDC only). UI may be prod while bolt is qa locally."""
    for key in (f"NEO4J_ENV_{app.upper()}", "NEO4J_ENV"):
        raw = os.environ.get(key)
        if raw and str(raw).strip():
            return str(raw).strip().lower()
    return ui_env


def _neo4j_yaml_for_env(app_cfg: dict, env: str) -> dict:
    """Per-env Neo4j host block; `neo4j:` in YAML, else legacy `memgraph:` (ICDC only today)."""
    bolt = app_cfg.get("neo4j") or app_cfg.get("memgraph") or {}
    per_env = dict(bolt.get(env) or {})
    if not per_env.get("endpoint") and env != "qa":
        per_env = dict(bolt.get("qa") or {})
    return per_env


def _expected_db_password(app: str, env: str, expected_source: str) -> str:
    """Password for Memgraph or Neo4j bolt (env only)."""
    if expected_source == "neo4j":
        app_u, env_u = app.upper(), env.upper()
        for key in (
            f"NEO4J_PASSWORD_{app_u}_{env_u}",
            f"NEO4J_PASSWORD_{app_u}",
            f"MEMGRAPH_PASSWORD_{app_u}_{env_u}",
            f"MEMGRAPH_PASSWORD_{app_u}",
        ):
            val = os.environ.get(key)
            if val:
                return val
        return ""
    return _memgraph_env(app, env, "password", "")


def _memgraph_env(app: str, env: str, field: str, yaml_value: str = "") -> str:
    """Resolve Memgraph endpoint / username / password for one app and environment.
    Password (each app has its own Memgraph cluster):
      1. MEMGRAPH_PASSWORD_{APP}_{ENV}   e.g. MEMGRAPH_PASSWORD_C3DC_QA
      2. MEMGRAPH_PASSWORD_{APP}         e.g. MEMGRAPH_PASSWORD_C3DC_QA2
    Endpoint / username also allow a global fallback:
    MEMGRAPH_ENDPOINT, MEMGRAPH_USERNAME (after per-app keys)
    YAML supplies endpoint/username defaults only; never passwords.
    """
    app_u, env_u = app.upper(), env.upper()
    field_u = field.upper()
    keys = [
        f"MEMGRAPH_{field_u}_{app_u}_{env_u}",
        f"MEMGRAPH_{field_u}_{app_u}",
    ]
    if field_u != "PASSWORD":
        keys.append(f"MEMGRAPH_{field_u}")
    for key in keys:
        val = os.environ.get(key)
        if val:
            return val
    return yaml_value or ""


# ---------------------------------------------------------------------------
# Config load and test environment
# ---------------------------------------------------------------------------


def load_config() -> dict:
    with open(CONFIG_FILE) as fh:
        return yaml.safe_load(fh)


def env_flag(name: str) -> bool | None:
    """Parse HEADLESS=false / HEADED=true style env vars; unset → None."""
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def resolve_test_env(cli_env: str | None = None) -> str:
    """pytest --env, then ENV, then default qa."""
    return (cli_env or os.environ.get("ENV") or DEFAULT_ENV).lower()


# ---------------------------------------------------------------------------
# Internal helpers (used by public getters above)
# ---------------------------------------------------------------------------


def _normalized_env(env: str | None) -> str:
    return (env or os.environ.get("ENV") or DEFAULT_ENV).lower()


def _app_config(app: str, cfg: dict) -> dict:
    apps = cfg.get("apps", {})
    if app not in apps:
        raise KeyError(f"App '{app}' is not defined in {CONFIG_FILE}")
    return apps[app]


# ---------------------------------------------------------------------------
# Public settings API (what tests and fixtures should call)
# ---------------------------------------------------------------------------


def get_browser_settings(cfg: dict = None, name: str = None, headless: bool | None = None) -> BrowserSettings:
    cfg = cfg or load_config()
    b = cfg.get("browser", {})
    if headless is None:
        headed = env_flag("HEADED")
        headless_env = env_flag("HEADLESS")
        if headed is not None:
            headless = not headed
        elif headless_env is not None:
            headless = headless_env
        else:
            headless = b.get("headless", True)
    return BrowserSettings(
        name=name or os.environ.get("BROWSER") or b.get("name", "chromium"),
        headless=headless,
        viewport=b.get("viewport", {"width": 1920, "height": 1080}),
        timeout_ms=int(os.environ.get("DEFAULT_TIMEOUT", b.get("timeout_ms", 30000))),
    )


def get_app_url(app: str, env: str | None = None, cfg: dict | None = None) -> str:
    """Portal URL for `app` in `env` (environments.yaml `urls:` + URL_{APP}_{ENV} override)."""
    cfg = cfg or load_config()
    env = _normalized_env(env)
    urls = _app_config(app, cfg).get("urls", {})
    url = os.environ.get(f"URL_{app.upper()}_{env.upper()}") or urls.get(env)
    if not url:
        raise ValueError(
            f"No URL for app={app} env={env}. Add it to {CONFIG_FILE} "
            f"or set URL_{app.upper()}_{env.upper()}."
        )
    return url


def get_db_settings(app: str, env: str | None = None, cfg: dict | None = None) -> DbSettings:
    """Bolt host/credentials for expected data (Memgraph or Neo4j per app `expected_source`)."""
    cfg = cfg or load_config()
    ui_env = _normalized_env(env)
    a = _app_config(app, cfg)
    expected_source = a.get("expected_source", "memgraph")
    bolt_env = ui_env
    if expected_source == "neo4j":
        bolt_env = neo4j_bolt_env(app, ui_env)
        nj = _neo4j_yaml_for_env(a, bolt_env)
        endpoint = _neo4j_env(app, bolt_env, "endpoint", nj.get("endpoint", ""))
        username = _neo4j_env(app, bolt_env, "username", nj.get("username", ""))
        password = _expected_db_password(app, bolt_env, expected_source)
    else:
        mg = (a.get("memgraph") or {}).get(ui_env, {})
        endpoint = _memgraph_env(app, ui_env, "endpoint", mg.get("endpoint", ""))
        username = _memgraph_env(app, ui_env, "username", mg.get("username", ""))
        password = _expected_db_password(app, ui_env, expected_source)
    return DbSettings(
        expected_source=expected_source,
        endpoint=endpoint,
        username=username,
        password=password,
        bolt_env=bolt_env,
    )


def get_app_settings(app: str, env: str | None = None, cfg: dict | None = None) -> AppSettings:
    """UI URL + bolt DB settings for fixtures (combines get_app_url and get_db_settings)."""
    from Commons.tab_setting import settings_for_app

    cfg = cfg or load_config()
    ui_env = _normalized_env(env)
    compare = settings_for_app(app)
    return AppSettings(
        app=app,
        env=ui_env,
        url=get_app_url(app, ui_env, cfg),
        db=get_db_settings(app, ui_env, cfg),
        tab_row_limit=compare.tab_row_limit,
        pagination_max_pages=compare.pagination_max_pages,
        tab_execution=dict(compare.tab_execution),
    )


def input_dir(app: str) -> Path:
    """Folder holding the input Excel files for an app (Katalon: InputFiles/<app>)."""
    return INPUTFILES_ROOT / app
