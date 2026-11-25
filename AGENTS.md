# Working in commons-automation

On `update-py-tests`, all eight apps execute `Testcases/<APP>/**/test_*.py`, not
Excel Steps. Read `docs/PYTHON_MIGRATION.md` for the current coverage and branch
differences before using the historical Excel inventory below. Query/static-data
workbooks remain under `InputFiles`; do not enable Excel testcase collection.

Read `docs/PROJECT_GUIDE.md` before changing this repository. It explains the
framework, seven apps, current test coverage, known exceptions, and validation
baseline. `docs/repository-index.json` is a searchable static snapshot of the
files, testcase steps, query locations, locators, models, and findings reviewed
on 2026-11-04. Filter the index to the relevant app or testcase rather than loading
the whole file. Re-read the actual source before relying on snapshot details.

## Project conventions

- Read the applicable `.cursor/rules/*.mdc` and app skill references before query
  or locator work. Some rules describe historical UI snapshots and legacy Python
  tests; reconcile them with current Python cases, code, configuration, and evidence.
- `Testcases/<APP>/.../test_*.py` contains each test's actions. The matching
  `InputFiles/<APP>/...xlsx` contains expected queries or static data. Resolve the
  `load_query_file()` argument; do not infer the input solely from its filename.
- Query-only requests belong in the specified input workbook and tab. Preserve
  unrelated cells, styles, testcase steps, configuration, and other cases.
- Resolve current environment, endpoint, row limit, enabled tabs, and UI filters
  before diagnosing a mismatch. `.env` overrides YAML without overriding already
  set shell variables; pytest CLI options override their corresponding defaults.
- Compare the same tab in both saved UI and DB output workbooks. The assertion
  summary alone is insufficient to identify the cause.
- Derive expected records from the real filters, relationships, backend indexing,
  ordering, and pagination. Do not add literal entity IDs or follow-up suffix
  lists solely to force agreement with one captured UI page. Existing snapshot
  workarounds are findings to investigate, not general query patterns.
- When a UI page has unspecified tie ordering, an explicitly parameterized query
  may bind displayed record identities at runtime. Keep study/filter predicates
  in the DB query and obtain every expected value independently from the DB.
  Never copy UI clinical values into expected output or save displayed ID lists.
- Scope counts correctly: filtered stat-bar totals can differ from whole-study
  Studies-tab totals. An entity filter may restrict that entity's tab as well as
  the participant cohort. Check the app and active filter.
- Keep C3DC and GC schemas, clusters, and credentials separate. Local C3DC
  `bolt://localhost:7687` is distinct from the default configured QA cluster.
- Use `ObjectRepository/<APP>/` for locators and filter tokens. App adapters are
  `Commons/apps/<app>/app.py`; Python testcases call their methods directly.
- Validate the changed query against the intended backend and rerun the exact
  testcase. For shared framework changes, run relevant unit tests and affected
  cases. Report skips and unperformed checks separately from passing checks.
- Do not change configuration or weaken comparisons just to obtain a green run.
  Preserve existing user edits and never copy secrets from `.env` into docs,
  reports, commands shown to the user, or committed files.

## Known baseline

On 2026-11-04 the latest unit run had 73 passes and two failures: GC and C3DC row-limit
tests assume 100 while YAML sets 15 and 13. INS Datasets also has a handler/adapter
method-name mismatch. Details are in the guide. These were observed, not repaired,
during the repository learning pass.
