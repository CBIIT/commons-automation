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

## Home page content

`static/TC01_PSDC_Verify_home_page_content.xlsx` checks the home page after
dismissing the warning banner. The `HomePage` sheet in
`InputFiles/PSDC/PSDC_StaticData.xlsx` contains 31 checks for the welcome banner,
four content panels, Explore/Read More/submission links, footer headings and
links, and email-signup labels. Link destinations are verified without opening
external sites or submitting the form. Release version numbers are not static
copy and are not included. Expected copy and locators were inspected on QA on
2026-11-13. The existing PSDC regression glob includes this testcase.

```bash
python3 -m pytest Testcases/PSDC/static/TC01_PSDC_Verify_home_page_content.xlsx --env qa -q
```

## About menu content

`static/TC02_PSDC_Verify_about_tab_content.xlsx` opens About, Access Data,
Analyze Data, and Support through the About menu. It verifies all four headings,
nine body paragraphs, and three link labels/URLs using `verify_static_data`,
then asserts that no checks failed. External links are checked without opening
them or launching an email client.

The expected copy was reviewed against QA and the supplied screenshots on
2026-11-13. It lives in `InputFiles/PSDC/PSDC_StaticData.xlsx`, with one
sheet per page, following the existing shared static-workbook contract. This
static input intentionally uses the adapter's `STATIC_DATA_EXCEL` name rather
than the study-query naming pattern. Locators live under
`ObjectRepository/PSDC/static/`; menu locators are scoped to the desktop header
because PSDC also renders hidden mobile controls with duplicate IDs.
The testcase is included by the existing PSDC regression `static/TC*.xlsx` glob.

```bash
python3 -m pytest Testcases/PSDC/static/TC02_PSDC_Verify_about_tab_content.xlsx --env qa -q
```

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

Additional PBCS cases select the study and one checkbox from the open screenshot
facets. Each has a matching input workbook with the same basename:

| Case | Filter group | Checkbox |
|---|---|---|
| TC02 | Studies/CancerTypes | breast |
| TC03 | Studies/CancerTypes | Not Applicable |
| TC04 | Studies/Countries | Poland |
| TC05 | Studies/BiospecimenCollection | Yes |
| TC06 | Participants/Race | white |
| TC07 | Participants/Ethnicity | not hispanic or latino |
| TC08 | Participants/Sex | female |

These filters select eligible studies. Their SQL keeps whole-study summary
counts and all Studies columns; it does not restrict those summaries to just
the individual participants matching the selected facet. Breast maps to the
source's `UBERON:0000310`; missing primary sites form Not Applicable. Each query
includes its own filter predicate, without retaining the TC01 Study Design
predicate. Age-range coverage is not included.

The new queries materialize the eligible-study selection once and aggregate
child tables independently to avoid join multiplication. They use SQLite's
`AS MATERIALIZED` syntax, which requires SQLite 3.35 or later. Counts and rows
still come from the TSVs, including all 11 displayed Studies columns.

Run this PBCS set on QA. Before using another environment, verify its URL and
that the expected TSV release matches its data.

## NLST checkbox filters

`studies/NLST/` contains one testcase per checkbox facet, each with a matching
`InputFiles/PSDC/` workbook using the same basename and title-case `Nlst` token.
Every case selects NLST and exactly one additional filter:

| Case | Filter group | Checkbox |
|---|---|---|
| TC01 | Studies/StudyDesign | Clinical Trial |
| TC02 | Studies/CancerTypes | lung |
| TC03 | Studies/Countries | United States of America |
| TC04 | Studies/BiospecimenCollection | Yes |
| TC05 | Participants/Race | american indian or alaska native |
| TC06 | Participants/Ethnicity | hispanic or latino |
| TC07 | Participants/Sex | male |

Each case compares the five numeric stat counts and all 11 Studies columns to
NLST's TSV data, using the same whole-study discovery semantics described above.
The lung predicate maps to source value `UBERON:0002048`. No age or other slider
interactions are included. All seven cases belong to regression; TC01 also
belongs to smoke through the existing suite patterns.

```bash
python3 -m pytest Testcases/PSDC/studies/NLST --env qa
```

## PLCO checkbox filters

`studies/PLCO/` contains one testcase per checkbox facet. Each selects PLCO and
one additional filter, with a matching input workbook and title-case `Plco`
filename token:

| Case | Filter group | Checkbox |
|---|---|---|
| TC01 | Studies/StudyDesign | Cohort Study - Prospective |
| TC02 | Studies/CancerTypes | prostate gland |
| TC03 | Studies/Countries | United States of America |
| TC04 | Studies/BiospecimenCollection | Yes |
| TC05 | Participants/Race | asian |
| TC06 | Participants/Ethnicity | not hispanic or latino |
| TC07 | Participants/Sex | female |

The prostate-gland source predicate uses `UBERON:0002367`. The queries select
eligible studies and retain PLCO's complete study summaries, rather than
counting only participants matching the selected facet. All seven cases compare
the five numeric stat counts and all 11 Studies columns against TSV data. No
slider interactions are included. TC01 is in smoke and regression; the other
six cases are in regression through the existing suite patterns.

```bash
python3 -m pytest Testcases/PSDC/studies/PLCO --env qa
```

## Unfiltered all-study comparison

`studies/All/TC01_PSDC_Study_All_StatbarAndTable.xlsx` opens Explore without
selecting any filters. Its matching input workbook compares the five numeric
stat counts and all 11 Studies columns for every loaded study, ordered by study
acronym. The prepared source snapshot contains NLST, PBCS, and PLCO.

Global cancer-type and collected-category counts are distinct across studies;
they are not the sums of per-study counts. Participants and files use their
study-scoped records. Data Volume retains the existing limitation documented in
`InputFiles/PSDC/README.md`: the loading manifests do not contain file sizes.

Prepare all three study snapshots, not only PBCS, before running this case:

```bash
python3 -m pytest Testcases/PSDC/studies/All --env qa
```

The existing suite patterns include this TC01 case in smoke and regression.
