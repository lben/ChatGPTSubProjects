# Deterministic toolbox

Prefer these commands over re-deriving workflows. Inspect each external command before first use.

| Tool | Command | Writes | Purpose |
|---|---|---:|---|
| Initialize | `tools\\agentctl.cmd init` or `sh tools/agentctl.sh init` | Local only | Create ignored runtime state from templates. |
| Harness doctor | `tools\\agentctl.cmd doctor` or `sh tools/agentctl.sh doctor` | Local only | Initialize, inspect runtime, and validate the harness. |
| Harness validate | `tools\\agentctl.cmd validate` or `sh tools/agentctl.sh validate` | No | Validate tracked contracts and existing local state. |
| Work status | `tools\\agentctl.cmd status` or `sh tools/agentctl.sh status` | Local only | Show the active task and Git state. |
| Fast verification | `tools\\agentctl.cmd verify fast` or `sh tools/agentctl.sh verify fast` | Test-dependent | Run allowlisted fast checks. |
| Full verification | `tools\\agentctl.cmd verify full` or `sh tools/agentctl.sh verify full` | Test-dependent | Run completion checks and the leak scan. |
| DB tool doctor | `tools\\dbtool.cmd doctor` or `sh tools/dbtool.sh doctor` | No | Validate the separate runner configuration and reachability. |
| DB query | `tools\\dbtool.cmd query --request <local-json> --output <local-json>` | Local only | Execute one reviewed request through the external runner. |
| Archive task | `tools\\agentctl.cmd archive-task` or `sh tools/agentctl.sh archive-task` | Local only | Archive a proven completed task and reset active state. |

## External tool rule

The external `run-db-query` command or REST service must live outside this repository. It owns authentication. Do not add credentials to this file, local configuration, commands, arguments, requests, output, or logs.

## Add a reusable tool

Stage a proposal under `.agent/local/pending/`. Include:

- exact argument-array command;
- required inputs;
- read and write effects;
- network and external-system effects;
- success condition;
- failure behavior;
- verification evidence;
- rollback.
