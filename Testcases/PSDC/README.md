# PSDC test authoring

The `psdc` fixture uses QA from `Config/environments.yaml`, the PSDC object
repository, and a lazy TSV source. The framework follows CTDC's Excel workflow:

1. Prepare an approved dated TSV release as described in
   [InputFiles/PSDC/README.md](../../InputFiles/PSDC/README.md).
2. Add an input workbook in `InputFiles/PSDC/` using the CTDC query-workbook
   format. Its `StudiesTab` TabQuery returns the Studies grid columns, and its
   StatQuery returns the expected counts for the selected filters.
3. Add a testcase workbook with a `Steps` sheet under
   `Testcases/PSDC/studies/<STUDY>/`. Row 2 identifies the input workbook, just
   as it does for CTDC. Static cases go under `Testcases/PSDC/static/`.

Typical steps after the input-workbook row:

| Action | Page | Params | Filter |
|---|---|---|---|
| accept_banner | | | |
| open_explore | | | |
| select_study | | NLST | |
| select_filter | Participants/Sex | | female |
| read_statbar | | | |
| verify_tab | | Studies | |
| assert_no_failures | | | |

The StudiesTab SQL column order is:
Study Acronym, Study Name, Enrollment Period, Study Period, Study Design,
Study Status, Cancer Types, Data Categories, Biospecimens, Enrollment Age,
Participants. Format displayed values such as `32 of 70` and `2002 - 2004`
in the query using approved TSV data. Match the UI's initial study-acronym sort
before applying the configured row limit.

StatQuery aliases are `Studies`, `Participants`, `Cancer Types`,
`Data Categories`, and `Study Files`. These are distinct concepts: the study
grid's Data Categories cell includes a denominator, while the stat bar shows
the number of categories represented in the filtered results.

The observed QA filters are registered under `Studies/Study`,
`Studies/StudyDesign`, `Studies/CancerTypes`, `Studies/Countries`,
`Studies/BiospecimenCollection`, `Participants/Race`,
`Participants/Ethnicity`, and `Participants/Sex`. Filter values match the
checkbox keys in `ObjectRepository/PSDC/filters/`.

`open_study` takes an acronym in Params. Use `click` with `Page=StudyDetails`
and Params such as `Demographics-Tab` or `StudyFiles-Tab` to navigate its
sections. Detail tabs are navigation locators, not Explore comparison tabs.

```bash
python3 -m pytest Testcases/PSDC --env qa
python3 -m pytest -m "psdc and smoke" --env qa
```

UI/expected workbooks are written to `OutputFiles/PSDC/QA/`. Row limits and
pagination caps live in `Config/tab_setting.yaml`.

Use `TC##_PSDC_Study_<Study>_<Filter>-<Value>.xlsx` for testcase and input
workbook names, with a title-case study token such as `Pbcs`. Both workbooks
share the same basename; output workbooks append `_UI` and `_DB`. Keep actual
study IDs in filters and SQL uppercase, such as `PBCS`.

The first case is `studies/PBCS/TC01_PSDC_Study_Pbcs_StudyDesign-CaseControl.xlsx`.
It selects PBCS and Case-Control Study, checks the five numeric stat counts, and
compares all 11 Studies grid columns to SQL over the supplied PBCS snapshot.
The snapshot's `source_manifest.json` records the archive members and encodings.
Enrollment age is converted from days to years. The category denominator follows
PSDC's display taxonomy, which excludes Sexual Orientation and Gender Identity;
the query counts the remaining source categories rather than hardcoding 70.

Only QA is configured; add verified environment URLs before running against
another environment.
