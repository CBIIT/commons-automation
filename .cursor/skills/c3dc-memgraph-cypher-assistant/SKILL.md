---
name: memgraph-cypher-assistant
description: Generate, validate, debug and test Memgraph Cypher queries.
---

# Purpose

This skill helps users:

1. Generate Cypher queries.
2. Debug failed queries.
3. Explain Memgraph errors.
4. Test generated queries using scripts/query_memgraph.py.
5. Suggest corrections based on references/backend-index-query/indices.yaml..

# Available References

## Backend Index Query
- references/backend-index-query/indices.yaml

## Database Model
- references/model/cds-model.yml
- references/model/cds-model-props.yml

# Available Script

- scripts/query_memgraph.py

# Workflow

When asked to generate/create/add a query:

1. If the user provides host, port, username, password, skip, and limit, replace the defaults with those values.
2. Read all files in the references/backend-index-query folder.
3. Read all files in the references/model folder.
4. If either the references/backend-index-query folder or the references/model folder has no files, stop and ask the user to provide references files.
5. Generate Cypher.
6. Execute using scripts/query_memgraph.py with the generated Cypher query.
7. If successful:
   - Return query.
   - Summarize results.
   - Show the results in table.
   - Validate results against the requirement.
8. If failed:
   - Parse error.
   - Identify failing clause.
   - Explain why.
   - Suggest corrected query.
   - Re-run until query succeeds.

When asked to test/debug/validate a query:

1. If the user provides host, port, username, password, skip, and limit, replace the defaults with those values.
2. Read all files in the references/backend-index-query folder.
3. Read all files in the references/model folder.
4. If either the references/backend-index-query folder or the references/model folder has no files, stop and ask the user to provide references files.
5. Execute using scripts/query_memgraph.py with given query.
6. If successful:
   - Return query.
   - Summarize results.
   - Show the results in table.
7. If failed:
   - Parse error.
   - Identify failing clause.
   - Explain why.
   - Suggest corrected query.
   - Re-run until query succeeds.

# Error Analysis Rules

For syntax errors:

- Locate exact clause.
- Explain Cypher syntax issue.
- Provide corrected version.

For schema errors:

Example:

Node label not found: study

Actions:
- Compare against Backend Index Query.
- Compare against  Database Model.
- Suggest valid labels.

For relationship errors:

Example:

Relationship HAS_FILE does not exist

Actions:
- Compare against Backend Index Query.
- Compare against Database Model.
- Suggest valid relationship types.

# Query Generation Rules
Always:

- Use parameterized Cypher.
- Include LIMIT.
- Avoid APOC.
- Validate labels and relationship names against files in Backend Index Query and Database Model.
- Test query with scripts/query_memgraph.py before returning.