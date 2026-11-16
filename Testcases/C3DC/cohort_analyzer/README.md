# Cohort Analyzer

Analyzer functions live in `Commons/apps/c3dc/cohort_analyzer.py`; locators live
in `ObjectRepository/C3DC/cohort_analyzer.yaml`. The app adapter and Excel profile
delegate to those functions. This folder is registered for C3DC Excel cases and
included in the C3DC regression suite.

`TC01_C3DC_Verify_Add_Example_Cohorts.xlsx` navigates through the Cohort Analyzer
link and clicks Add Example Cohorts exactly once from an empty cohort list.
Verification requires three distinct example entries with the expected names,
positive participant counts, selected checkbox images, and a `3/3` selector.
Participant counts can vary and are not hardcoded. Expected names are in the
testcase's Filter cell, separated by semicolons. Each browser context is isolated;
no database or input workbook is needed.

Run visibly on production while QA is unavailable:

```bash
python3 -m pytest "Testcases/C3DC/cohort_analyzer/TC01_C3DC_Verify_Add_Example_Cohorts.xlsx" --env prod --headed --slowmo 1000 -s
```
