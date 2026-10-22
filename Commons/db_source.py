"""Run Cypher from input Excel against Bolt (Memgraph or Neo4j) and return expected tables for UI compare."""
import json
from dataclasses import dataclass, field
from typing import List, Optional

from Commons import action_log
from Commons.tab_setting import apply_tab_row_limit
from Commons.query_reader import QueryFile
from Commons.settings import AppSettings, memgraph_password_env_keys, neo4j_password_env_keys


def memgraph_tab_query_label(tab_key: str, display_name: Optional[str] = None) -> str:
    """Console label for [DB] … when running a result-tab Cypher query."""
    name = (display_name or "").strip()
    if not name:
        name = tab_key[:-3] if tab_key.endswith("Tab") else tab_key
    return f"{name} tab query from memgraph"


def neo4j_tab_query_label(tab_key: str, display_name: Optional[str] = None) -> str:
    name = (display_name or "").strip()
    if not name:
        name = tab_key[:-3] if tab_key.endswith("Tab") else tab_key
    return f"{name} tab query from neo4j"


@dataclass
class Table:
    header: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)


class ExpectedDataSource:
    """Expected UI results from the app's bolt DB (see get_db_settings)."""

    def fetch_tab_table(
        self, query_file: QueryFile, tab_key: str, tab_display_name: Optional[str] = None
    ) -> Table:
        raise NotImplementedError

    def fetch_stat_bar_table(self, query_file: QueryFile) -> Table:
        raise NotImplementedError


def format_db_cell(value) -> str:
    """Convert one bolt result value to the string form used in compare (Katalon/Java export rules)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return str(value)


# Backward-compatible alias
format_memgraph_cell = format_db_cell


class MemgraphSource(ExpectedDataSource):
    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        app: str = "",
        env: str = "",
        tab_row_limit: Optional[int] = None,
    ):
        missing = []
        if not endpoint:
            missing.append("Memgraph endpoint (Config/environments.yaml or MEMGRAPH_ENDPOINT_<APP>)")
        if not username:
            missing.append("Memgraph username (Config/environments.yaml or MEMGRAPH_USERNAME_<APP>)")
        if not password:
            per_env, per_app = memgraph_password_env_keys(app or "APP", env or "qa")
            missing.append(f"Memgraph password ({per_env} or {per_app})")
        if missing:
            raise RuntimeError(
                "Memgraph connection is not configured for this test app:\n  - "
                + "\n  - ".join(missing)
                + "\nPasswords are per application (C3DC and GC differ). Put them in gitignored .env."
            )
        self.endpoint, self.username, self.password = endpoint, username, password
        self._app, self._env = app, env
        self._tab_row_limit = tab_row_limit
        self._driver = None
        self._logged_connection = False

    def get_bolt_driver(self):
        """Open the Bolt driver on first use (no TLS, same as ConnectMemgraph.groovy)."""
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self.endpoint,
                auth=(self.username, self.password),
                encrypted=False,
            )
        return self._driver

    def _tab_cypher(self, query_file: QueryFile, tab_key: str) -> str:
        raw = query_file.query_for_tab(tab_key)
        return apply_tab_row_limit(raw, self._tab_row_limit)

    def run_cypher_as_table(self, cypher: str, query_label: str = "tab query from memgraph") -> Table:
        """Execute Cypher and return header + rows as strings."""
        if not self._logged_connection:
            action_log.memgraph_connection(self.username, self.endpoint)
            self._logged_connection = True
        action_log.memgraph_query(query_label, cypher)
        try:
            with self.get_bolt_driver().session() as session:
                records = list(session.run(cypher))
        except Exception as exc:
            msg = str(exc)
            if "Unauthenticated" in msg or "Authentication failure" in msg:
                per_env, per_app = memgraph_password_env_keys(self._app or "APP", self._env or "qa")
                raise RuntimeError(
                    f"Memgraph rejected login for {self._app or 'app'} ({self.username!r} @ {self.endpoint}). "
                    f"Set {per_app} or {per_env} to the password for that cluster (not a shared MEMGRAPH_PASSWORD)."
                ) from exc
            raise
        if not records:
            return Table()
        header = list(records[0].keys())
        table = Table(
            header=header,
            rows=[[format_db_cell(record[column]) for column in header] for record in records],
        )
        action_log.memgraph_db_table(table.header, table.rows)
        return table

    def fetch_tab_table(
        self, query_file: QueryFile, tab_key: str, tab_display_name: Optional[str] = None
    ) -> Table:
        """Run the TabQuery for one result tab (e.g. ParticipantsTab) from the input Excel."""
        cypher = self._tab_cypher(query_file, tab_key)
        label = memgraph_tab_query_label(tab_key, tab_display_name)
        return self.run_cypher_as_table(cypher, label)

    def fetch_stat_bar_table(self, query_file: QueryFile) -> Table:
        """Run the StatQuery from the input Excel for stat-bar verification."""
        if not query_file.stat_bar_query:
            raise ValueError(f"{query_file.path.name} has no StatQuery")
        return self.run_cypher_as_table(query_file.stat_bar_query, "Stat bar query from memgraph")

    def close_connection(self):
        """Close the Bolt driver when the test session ends."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def close(self):
        """Alias for pytest fixture teardown."""
        self.close_connection()


class Neo4jSource(MemgraphSource):
    """Expected data via Neo4j Bolt (ICDC today; same driver as MemgraphSource)."""

    def __init__(
        self,
        endpoint: str,
        username: str,
        password: str,
        app: str = "",
        env: str = "",
        ui_env: str = "",
        tab_row_limit: Optional[int] = None,
    ):
        missing = []
        if not endpoint:
            missing.append(
                "Neo4j endpoint (Config/environments.yaml apps.<APP>.neo4j or NEO4J_ENDPOINT_<APP>)"
            )
        if not username:
            missing.append(
                "Neo4j username (Config/environments.yaml apps.<APP>.neo4j or NEO4J_USERNAME_<APP>)"
            )
        if not password:
            per_env, per_app = neo4j_password_env_keys(app or "APP", env or "qa")
            missing.append(f"Neo4j password ({per_env} or {per_app})")
        if missing:
            raise RuntimeError(
                "Neo4j connection is not configured for this test app:\n  - "
                + "\n  - ".join(missing)
                + "\nPut the password in gitignored `.env` (NEO4J_PASSWORD_<APP>)."
            )
        self.endpoint, self.username, self.password = endpoint, username, password
        self._app, self._env = app, env
        self._ui_env = ui_env or env
        self._tab_row_limit = tab_row_limit
        self._driver = None
        self._logged_connection = False

    def run_cypher_as_table(self, cypher: str, query_label: str = "tab query from neo4j") -> Table:
        if not self._logged_connection:
            action_log.memgraph_connection(self.username, self.endpoint)
            self._logged_connection = True
        action_log.memgraph_query(query_label, cypher)
        try:
            with self.get_bolt_driver().session() as session:
                records = list(session.run(cypher))
        except Exception as exc:
            msg = str(exc)
            if "Unauthenticated" in msg or "Authentication failure" in msg:
                per_env, per_app = neo4j_password_env_keys(self._app or "APP", self._env or "qa")
                raise RuntimeError(
                    f"Neo4j rejected login for {self._app or 'app'} ({self.username!r} @ {self.endpoint}). "
                    f"Set {per_app} or {per_env} (or MEMGRAPH_PASSWORD_{self._app or 'APP'})."
                ) from exc
            if (
                exc.__class__.__name__ in ("ServiceUnavailable", "ValueError")
                or "ServiceUnavailable" in msg
                or "Cannot resolve address" in msg
                or "nodename nor servname" in msg
            ):
                bolt_hint = (
                    f"bolt env={self._env}"
                    if self._env == self._ui_env
                    else f"UI env={self._ui_env}, bolt env={self._env} (NEO4J_ENV / NEO4J_ENV_{self._app})"
                )
                raise RuntimeError(
                    f"Cannot reach Neo4j at {self.endpoint} ({bolt_hint}). "
                    "Hosts are on the NCI network — use VPN or run from an NCI machine. "
                    "For local runs against QA data while testing another UI env, set NEO4J_ENV=qa in `.env`. "
                    "Or run pytest with `--env qa` so UI and Neo4j both use QA. "
                    "Override host with NEO4J_ENDPOINT_<APP>_<ENV>. "
                    f"Original error: {msg}"
                ) from exc
            raise
        if not records:
            return Table()
        header = list(records[0].keys())
        table = Table(
            header=header,
            rows=[[format_db_cell(record[column]) for column in header] for record in records],
        )
        action_log.memgraph_db_table(table.header, table.rows)
        return table

    def fetch_tab_table(
        self, query_file: QueryFile, tab_key: str, tab_display_name: Optional[str] = None
    ) -> Table:
        query = self._tab_cypher(query_file, tab_key)
        label = neo4j_tab_query_label(tab_key, tab_display_name)
        return self.run_cypher_as_table(query, label)

    def fetch_stat_bar_table(self, query_file: QueryFile) -> Table:
        if not query_file.stat_bar_query:
            raise ValueError(f"{query_file.path.name} has no StatQuery")
        return self.run_cypher_as_table(query_file.stat_bar_query, "Stat bar query from neo4j")


def create_expected_data_source(settings: AppSettings) -> ExpectedDataSource:
    db = settings.db
    if db.expected_source == "memgraph":
        return MemgraphSource(
            db.endpoint,
            db.username,
            db.password,
            app=settings.app,
            env=db.bolt_env or settings.env,
            tab_row_limit=settings.tab_row_limit,
        )
    if db.expected_source == "neo4j":
        bolt_env = db.bolt_env or settings.env
        return Neo4jSource(
            db.endpoint,
            db.username,
            db.password,
            app=settings.app,
            env=bolt_env,
            ui_env=settings.env,
            tab_row_limit=settings.tab_row_limit,
        )
    raise ValueError(
        f"Unknown expected_source '{db.expected_source}' for {settings.app}. "
        "Supported: memgraph, neo4j."
    )


class LazySource(ExpectedDataSource):
    """Defer bolt DB connect until the first tab or stat-bar fetch (browser can start without a password)."""

    def __init__(self, settings: AppSettings):
        self._settings = settings
        self._connected: Optional[ExpectedDataSource] = None

    def get_connected_source(self) -> ExpectedDataSource:
        if self._connected is None:
            self._connected = create_expected_data_source(self._settings)
        return self._connected

    def fetch_tab_table(
        self, query_file: QueryFile, tab_key: str, tab_display_name: Optional[str] = None
    ) -> Table:
        return self.get_connected_source().fetch_tab_table(
            query_file, tab_key, tab_display_name=tab_display_name
        )

    def fetch_stat_bar_table(self, query_file: QueryFile) -> Table:
        return self.get_connected_source().fetch_stat_bar_table(query_file)

    def close(self):
        if self._connected is not None and hasattr(self._connected, "close_connection"):
            self._connected.close_connection()
