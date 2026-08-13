---
name: run-db-query
description: Execute one reviewed bounded read-only database request through the separate trusted run-db-query command or loopback REST service without handling credentials. Use only for approved reconciliation experiments.
disable-model-invocation: true
argument-hint: '[request file under .agent/local/db-requests/]'
---

# Run DB query

## Preconditions

1. Read `AGENTS.md` and `.agent/DB_TOOL_CONTRACT.md`.
2. Confirm `.agent/local/LOCAL_TOOLING.json` is configured.
3. Confirm the request is under `.agent/local/db-requests/`.
4. Confirm no credential field or connection string exists in the request.
5. Confirm one read-only experiment, target scope, timeout, row limit, and expected output.
6. Obtain user approval when the request is new, broader, sensitive, expensive, or can return raw rows.

## Execute

Use only:

```text
tools\\dbtool.cmd query --request <request> --output <result>
```

or:

```text
sh tools/dbtool.sh query --request <request> --output <result>
```

Do not invoke a native database client, `curl`, PowerShell web request, or a replacement script. Do not inspect authentication material or the runner internals.

## Handle output

- Save output only under `.agent/local/db-results/`.
- Read only the fields required by the experiment.
- Prefer aggregate metrics.
- Do not paste raw rows into chat or durable memory.
- Sanitize errors. Stop if the runner asks for credentials or returns connection details.
- Update the local reconciliation ledger with compact evidence and limitations.
