# BENTO pytest layout

Same idea as **`Testcases/C3DC/studies/<dbGaP>/`**: the **arm** is the study key.

| Folder | UI arm filter |
|--------|----------------|
| `arm-a/` | `A: RS 0-10, assigned endocrine therapy alone` |
| `arm-b/` | `B: RS 11-25, randomized to endocrine therapy alone` |
| `arm-c/` | `C: RS 11-25, randomized to chemo + endocrine therapy` |
| `arm-d/` | `D: RS > 25, assigned to chemo +` |

Each folder has **14 tests** (TC01–TC14): **Arm + one sidebar facet**. For each facet, **arm-a / arm-b / arm-c / arm-d use four different checkboxes** (e.g. Diagnosis: Adenocarcinoma, Comedocarcinoma, Not Reported, Tubular Carcinoma). See `Commons/bento_arm_filters.py` → `BENTO_FACET_SPECS`.

Facet list and workbook file names: `Commons/bento_arm_filters.py`. Expected data workbooks are flat under **`InputFiles/BENTO/`** (not grouped by arm folder). Explore steps are **`TC*.xlsx`** under each `arm-*/` folder (excel mode). Edit Steps in Excel or reconvert from Python with `Tools/convert_study_tests_to_excel.py Bento` if you still have `test_*.py`.

```bash
pytest Testcases/BENTO/arm-a -m bento
pytest Testcases/BENTO -m bento
```
