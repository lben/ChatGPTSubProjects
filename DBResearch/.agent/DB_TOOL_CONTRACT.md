# External run-db-query contract

`DBResearch` does not connect to the database directly. It delegates one reviewed request at a time to a separate trusted runner.

## Security invariant

The runner owns database authentication. No database username, password, token, DSN, connection string, or credential path may appear in:

- this repository;
- `.agent/local/LOCAL_TOOLING.json`;
- request JSON;
- command arguments;
- standard output;
- result JSON;
- Copilot prompts or memory.

## Supported transport A: external command

Preferred when the runner has its own secure credential integration.

Local configuration:

```json
{
  "transport": "command",
  "argv": [
    "C:\\absolute\\path\\outside\\DBResearch\\run-db-query.exe",
    "--request",
    "{request}",
    "--output",
    "{output}"
  ],
  "timeout_seconds": 60,
  "max_result_bytes": 5000000
}
```

Rules:

- use an argument array, not a shell command string;
- keep the executable or trusted script outside this workspace;
- let the runner write the result file;
- return a nonzero exit code on failure;
- do not print credentials or raw result rows to the terminal.

## Supported transport B: loopback REST

Local configuration:

```json
{
  "transport": "rest",
  "base_url": "http://127.0.0.1:8765",
  "health_path": "/health",
  "query_path": "/v1/query",
  "timeout_seconds": 60,
  "max_request_bytes": 1000000,
  "max_result_bytes": 5000000
}
```

`tools/dbtool.py` rejects non-loopback URLs. The REST service must keep database authentication internally.

## Request format

Store requests under `.agent/local/db-requests/`.

```json
{
  "request_id": "E001",
  "purpose": "Measure one candidate mapping",
  "operation": "query",
  "sql": "SELECT ...",
  "limits": {
    "timeout_seconds": 30,
    "max_rows": 2000,
    "result_mode": "aggregate"
  }
}
```

The exact SQL dialect is runner-specific. A request must contain one bounded read-only experiment. Do not include credentials or raw source-file contents.

## Result format

Store results under `.agent/local/db-results/`.

A result should include compact structured evidence:

```json
{
  "request_id": "E001",
  "status": "ok",
  "row_count": 1,
  "truncated": false,
  "elapsed_ms": 812,
  "columns": ["tested", "unique_matches", "ambiguous_matches", "unmatched"],
  "rows": [[2000, 1968, 9, 23]]
}
```

Prefer aggregate metrics. If raw rows are required, obtain explicit user approval and return the smallest permitted sample.

## Runner-side controls

The separate project should enforce:

- read-only database permissions;
- approved databases and schemas;
- one statement when practical;
- timeout, row, and byte limits;
- no DDL, DML, external commands, file access, or unsafe procedures;
- sanitized errors;
- audit records without secrets.

The harness instructions are not a substitute for server-side enforcement.
