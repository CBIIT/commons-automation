"""
Central config for tests: environment, URLs, Memgraph, browser, and folder paths.

Loads Config/environments.yaml (GC/C3DC URLs and Memgraph host per env; no secrets).
Optional gitignored .env supplies Memgraph passwords (per-app or global) without overriding
shell env vars. pytest --env / ENV pick qa | stage | prod; paths include InputFiles/
OutputFiles/<app>/<ENV>/ for UI/DB Excel (gitignored; created on write). Katalon: Profiles (*.glbl).
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


@dataclass
class BrowserSettings:
    name: str = "chromium"
    headless: bool = True
    viewport: dict = field(default_factory=lambda: {"width": 1920, "height": 1080})
    timeout_ms: int = 30000


@dataclass
class AppSettings:
    """Everything a test needs to know about one app in one environment."""
    app: str
    env: str
    url: str
    expected_source: str = "memgraph"      # Cypher against Memgraph (C3DC and GC)
    memgraph_endpoint: str = ""
    memgraph_username: str = ""
    memgraph_password: str = ""          # env only (see _memgraph_env); never from YAML


def memgraph_password_env_keys(app: str, env: str) -> tuple[str, str]:
    """Env var names to set Memgraph password for this app (per-cluster; no shared password)."""
    app_u, env_u = app.upper(), env.upper()
    return (
        f"MEMGRAPH_PASSWORD_{app_u}_{env_u}",
        f"MEMGRAPH_PASSWORD_{app_u}",
    )


def _memgraph_env(app: str, env: str, field: str, yaml_value: str = "") -> str:
    """Resolve Memgraph endpoint / username / password for one app and environment.

    Password (each app has its own Memgraph cluster):
      1. MEMGRAPH_PASSWORD_{APP}_{ENV}   e.g. MEMGRAPH_PASSWORD_C3DC_QA
      2. MEMGRAPH_PASSWORD_{APP}         e.g. MEMGRAPH_PASSWORD_C3DC

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


def load_config() -> dict:
    with open(CONFIG_FILE) as fh:
        return yaml.safe_load(fh)


def get_browser_settings(cfg: dict = None, name: str = None, headless: bool = None) -> BrowserSettings:
    cfg = cfg or load_config()
    b = cfg.get("browser", {})
    return BrowserSettings(
        name=name or os.environ.get("BROWSER") or b.get("name", "chromium"),
        headless=b.get("headless", True) if headless is None else headless,
        viewport=b.get("viewport", {"width": 1920, "height": 1080}),
        timeout_ms=int(os.environ.get("DEFAULT_TIMEOUT", b.get("timeout_ms", 30000))),
    )


def get_app_settings(app: str, env: str = None, cfg: dict = None) -> AppSettings:
    """Resolve URL / data source / DB endpoint for `app` (e.g. 'C3DC') in `env` (e.g. 'qa')."""
    cfg = cfg or load_config()
    env = (env or os.environ.get("ENV") or DEFAULT_ENV).lower()
    apps = cfg.get("apps", {})
    if app not in apps:
        raise KeyError(f"App '{app}' is not defined in {CONFIG_FILE}")
    a = apps[app]
    urls = a.get("urls", {})
    url = os.environ.get(f"URL_{app.upper()}_{env.upper()}") or urls.get(env)
    if not url:
        raise ValueError(f"No URL for app={app} env={env}. Add it to {CONFIG_FILE} "
                         f"or set URL_{app.upper()}_{env.upper()}.")
    mg = (a.get("memgraph") or {}).get(env, {})
    return AppSettings(
        app=app,
        env=env,
        url=url,
        expected_source=a.get("expected_source", "memgraph"),
        memgraph_endpoint=_memgraph_env(app, env, "endpoint", mg.get("endpoint", "")),
        memgraph_username=_memgraph_env(app, env, "username", mg.get("username", "")),
        memgraph_password=_memgraph_env(app, env, "password", ""),
    )


def input_dir(app: str) -> Path:
    """Folder holding the input Excel files for an app (Katalon: InputFiles/<app>)."""
    return INPUTFILES_ROOT / app
