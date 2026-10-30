# Excel-driven test cases

One **ExcelCaseProfile** per app. Pytest runs `TC*.xlsx` under each profile’s `case_subdirs` (e.g. `studies/`, `INS/Programs/CancerType/`) when `framework.test_case_source: excel`.

## Add a new app (INS, C3DC, …)

1. Copy `apps/ctdc.py` → `apps/<dir>.py` (use `Testcases` folder name, e.g. `INS`, `C3DC`, `BENTO`).
2. Set `app_key` (matches `BaseApp.NAME`), `fixture`, `input_files_prefix`, `excel_actions`, and `case_subdirs` (default `("studies",)`; Bento uses `arm-a`, …). `parse_test_function` is optional legacy (AST); new cases are authored as `TC*.xlsx` Steps sheets.
3. Add app-only step handlers in `extra_handlers` if needed (see `apps/gc.py` `multi_function`).
4. Import the module in `apps/__init__.py`.
5. Add `Testcases/<APP>/…/TC*.xlsx` with a **Steps** sheet (row 2 = input workbook path; actions from `excel_actions`).

Shared steps (`select_filter`, `verify_tab`, …) live in `_common_steps.py` — change only when all apps need the same behavior.
