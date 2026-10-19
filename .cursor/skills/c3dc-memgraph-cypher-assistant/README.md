# Introduction

Agent skill for generating and validating Memgraph Cypher queries. It helps backend developers produce error-free queries that match the format and schema of existing backend index queries and model files.

# Instruction

## Prepare references file

- Put the existing backend indices query file(i.e. indices.yaml) to the references/backend-index-query folder.
- Put the database model files(i.e. cds-model.yml, cds-model-props.yml) to the references/model folder.

## Set up Memgraph connection

- Ensure Memgraph is running and reachable.
- Use `scripts/query_memgraph.py` to execute queries.
- Defaults: host `127.0.0.1`, port `7687`, username `user`, password `password`, skip `0`, limit `5`.
- Override host, port, username, password, skip, and limit when provided.

## Generate a query

- Ask the agent to generate/create/add a Cypher query for your requirement.
- The agent reads the reference files, generates parameterized Cypher with `LIMIT`, and runs it via `scripts/query_memgraph.py`.
- On success: returns the query, summarizes results, and validates against the requirement.
- On failure: explains the error, suggests a fix, and re-runs until it succeeds.
- The user can override host, port, username, password, skip, and limit when asking the agent.

## Test/debug/validate a query

- Ask the agent to test, debug, or validate an existing Cypher query.
- The agent reads the reference files and runs the query via `scripts/query_memgraph.py`.
- On success: returns the query and summarizes results.
- On failure: explains the error, suggests a fix, and re-runs until it succeeds.
- The user can override host, port, username, password, skip, and limit when asking the agent.
