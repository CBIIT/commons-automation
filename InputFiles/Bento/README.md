# BENTO input workbooks

All query workbooks live **flat** in this folder (`InputFiles/BENTO/`), same as GC/C3DC top-level `TC*.xlsx` names. The arm is encoded in the file name, e.g. `TC01_Bento_arm-a_Diagnosis-Adenocarcinoma.xlsx`.

| Also here | Purpose |
|-----------|---------|
| `Bento_StaticData.xlsx` | Static page checks |

Testcase Steps live under `Testcases/BENTO/arm-*/`; edit query workbooks here directly. Arm/facet naming matrix: `Commons/bento_arm_filters.py`.

`TabQuery` / `StatQuery` are Neo4j Cypher (`expected_source: neo4j` in `Config/environments.yaml`).

Credentials: `BENTO_DB_PASSWORD_<ENV>`, optional `NEO4J_ENDPOINT_BENTO`, `URL_BENTO_QA` in `.env`.
