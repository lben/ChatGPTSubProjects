# Optional enterprise features

The base project does not depend on these features.

## MCP replacement for run-db-query

After the command or REST pilot is stable, the company can expose structured read-only tools instead of arbitrary SQL:

- search catalog candidates;
- describe columns and constraints;
- profile a candidate;
- run a bounded match experiment;
- validate a holdout;
- return aggregate metrics.

Give the DB Scout agent only that MCP tool set. Keep authentication, authorization, row limits, schema allowlists, and audit inside the company service.

## Hooks

Useful reviewed hooks can:

- block writes to tracked knowledge during normal work;
- run the sensitive-content scan before commits;
- reject destructive terminal commands;
- record sanitized audit events.

Start in report-only mode. Do not enable blocking behavior until the hook contract and failure path are tested in the managed VS Code version.

## Organization distribution

After a successful pilot, administrators can distribute approved instructions, agents, and skills at organization level. Keep work-specific state local to each approved workspace.
