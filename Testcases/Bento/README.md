# BENTO pytest layout

Same idea as **`Testcases/C3DC/studies/<dbGaP>/`**: the **arm** is the study key.

| Folder | UI arm filter |
|--------|----------------|
| `arm-a/` | `A: RS 0-10, assigned endocrine therapy alone` |
| `arm-b/` | `B: RS 11-25, randomized to endocrine therapy alone` |
| `arm-c/` | `C: RS 11-25, randomized to chemo + endocrine therapy` |
| `arm-d/` | `D: RS > 25, assigned to chemo +` |

Each folder has **14 tests** (TC01–TC14): **Arm + one sidebar facet**. For each facet, **arm-a / arm-b / arm-c / arm-d use four different checkboxes** (e.g. Diagnosis: Adenocarcinoma, Comedocarcinoma, Not Reported, Tubular Carcinoma).

Each Python testcase contains its facet selection and input workbook name. Expected data workbooks are flat under **`InputFiles/Bento/`**. Edit the Python tests directly, using explicit `select_filter` lines and separate `verify_tab("Cases")` calls.

```bash
pytest Testcases/Bento/arm-a -m bento
pytest Testcases/Bento -m bento
```
