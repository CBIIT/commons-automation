# BENTO pytest layout

Same idea as **`Testcases/C3DC/studies/<dbGaP>/`**: the **arm** is the study key.

| Folder | UI arm filter |
|--------|----------------|
| `arm-a/` | `A: RS 0-10, assigned endocrine therapy alone` |
| `arm-b/` | `B: RS 11-25, randomized to endocrine therapy alone` |
| `arm-c/` | `C: RS 11-25, randomized to chemo + endocrine therapy` |
| `arm-d/` | `D: RS > 25, assigned to chemo +` |

Each folder has **14 tests** (TC01–TC14): **Arm + one sidebar facet**. Each workbook's **Steps** sheet defines its arm and facet selections; filter locators live in `ObjectRepository/BENTO/filters/`.

Expected data workbooks are flat under **`InputFiles/BENTO/`** (not grouped by arm folder). Explore steps are **`TC*.xlsx`** under each `arm-*/` folder; edit the **Steps** sheet in Excel.

```bash
pytest Testcases/BENTO/arm-a -m bento
pytest Testcases/BENTO -m bento
```
