# Bounded Local Memory

Keep this file small. Store only durable, frequently useful, evidence-supported local facts.

Do not store credentials, raw rows, source-file contents, SQL result payloads, temporary task state, or information that should enter a tracked file.

## Project facts

## Environment and constraints

- Package installation may be unavailable on the managed workstation.
- Database access is delegated to the separate `run-db-query` runner.

## Stable conventions

- Work-specific state remains under `.agent/local/`.
- Aggregate evidence is preferred over raw rows.

## Known defenses

- Never place authentication material in prompts, files, command arguments, or query requests.
