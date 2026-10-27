# BENTO input workbooks

All query workbooks live **flat** in this folder (`InputFiles/BENTO/`), same as GC/C3DC top-level `TC*.xlsx` names. The arm is encoded in the file name, e.g. `TC01_Bento_arm-a_Diagnosis-Adenocarcinoma.xlsx`.

| Also here | Purpose |
|-----------|---------|
| `Bento_StaticData.xlsx` | Static page checks |

Regenerate tests and Cypher workbooks from Katalon sources:

```bash
python Tools/generate_bento_arm_tests.py
```

Refresh Cypher only (after editing `Commons/bento_cypher_queries.py`):

```bash
python Tools/convert_bento_sql_to_cypher.py
```

`TabQuery` / `StatQuery` are Neo4j Cypher (`expected_source: neo4j` in `Config/environments.yaml`).

Credentials: `NEO4J_PASSWORD_BENTO`, optional `NEO4J_ENDPOINT_BENTO`, `URL_BENTO_QA` in `.env`.
