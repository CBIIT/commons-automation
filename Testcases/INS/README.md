# INS pytest layout

| Folder | Excel testcase (`test_case_source: excel`) | Python (legacy) |
|--------|--------------------------------------------|-----------------|
| `Programs/CancerType/` | `TC01_…` – `TC23_…` Steps workbooks | — |
| `Programs/SpecialTopic/` | `TC01_…` – `TC06_…` | — |
| `DataSets/` | `TC01_…` – `TC03_…` (repository filters + `verify_datasets_tab`) | — |
| `static/` | `TC01_INS_StaticData.xlsx` (`verify_static_data` + navbar clicks) | — |

Query workbooks: flat under `InputFiles/INS/TC*.xlsx`. Static expected copy: `InputFiles/INS/INS_StaticData.xlsx`. TSV data: commit `Programs.zip` and `DataSetsTab.zip` only (see `InputFiles/INS/README.md`).

```bash
pytest Testcases/INS/Programs/CancerType -m ins --env qa
pytest Testcases/INS/Programs/CancerType/TC01_INS_CancerType-BladderCancer.xlsx -m ins --env qa
pytest Testcases/INS/static -m static --env qa
```
