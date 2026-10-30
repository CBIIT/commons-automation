# BENTO input workbooks

All query workbooks live **flat** in this folder (`InputFiles/BENTO/`), same as GC/C3DC top-level `TC*.xlsx` names. The arm is encoded in the file name, e.g. `TC01_Bento_arm-a_Diagnosis-Adenocarcinoma.xlsx`.

| Also here | Purpose |
|-----------|---------|
| `Bento_StaticData.xlsx` | Static page checks |

Edit `TabQuery` / `StatQuery` Cypher in each `TC*.xlsx` directly (`expected_source: neo4j` in `Config/environments.yaml`). Reference queries: `Commons/bento_cypher_queries.py`.

Credentials: `NEO4J_PASSWORD_BENTO`, optional `NEO4J_ENDPOINT_BENTO`, `URL_BENTO_QA` in `.env`.
