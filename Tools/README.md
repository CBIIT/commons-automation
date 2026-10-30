# Tools (maintainer scripts)

Not imported at pytest runtime. Use when refreshing locators, query workbooks, or Excel testcase Steps.

## Excel testcase Steps (`Testcases/.../TC*.xlsx`)

```bash
python3 Tools/convert_study_tests_to_excel.py <APP_KEY>   # GC, C3DC, CTDC, ICDC, Bento
python3 Tools/convert_study_tests_to_excel.py GC --keep-py
```

Requires `Commons/excel_testcase/apps/<app>.py`. See `Commons/excel_testcase/README.md`.

## Object repository (from Katalon export)

```bash
python3 Tools/convert_object_repository.py --katalon ../Commons_Automation --apps C3DC GC
python3 Tools/build_ctdc_object_repository.py
python3 Tools/build_icdc_object_repository.py
python3 Tools/build_ins_filters.py
```

## Query / expected-data workbooks (`InputFiles/.../TC*.xlsx`)

```bash
python3 Tools/convert_ctdc_sql_to_cypher.py [--dry-run]
python3 Tools/convert_icdc_sql_to_cypher.py [--dry-run]
python3 Tools/convert_bento_sql_to_cypher.py
```

SQL→Cypher helpers live in `Tools/cypher/`.
