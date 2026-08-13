# DBResearch

A repository-local operating system for GitHub Copilot in a managed VS Code workstation.
It is specialized for data investigation and reconciliation.

The project gives Copilot:

- durable local task state;
- bounded local memory;
- reusable Agent Skills;
- separate implementation, database, review, and learning roles;
- deterministic verification commands;
- a controlled improvement loop;
- a safe integration contract for an external `run-db-query` service.

It does not store database credentials, bypass company controls, or train the model.

## Important security boundary

This source repository is public. Treat every tracked file as public.

Work-specific state is stored under `.agent/local/`. Git ignores that directory. Put company names, file paths, table names, column names, hypotheses, query requests, and query results only there.

Never add company data, credentials, connection strings, database hostnames, or raw query results to a tracked file. Run the security scan before each commit.

Read [SECURITY.md](SECURITY.md) before connecting the database tool.

## Start

1. Download or clone `ChatGPTSubProjects`.
2. Open the `DBResearch` folder itself in VS Code.
3. Run **Tasks: Run Task → Harness: Initialize**.
4. Run **Tasks: Run Task → Harness: Doctor**.
5. Open Copilot Chat and select **Workmate**.
6. Start with:

```text
/reconcile-data

Investigate this file and find the most likely database key mapping:
<local file path>
```

If custom agents or skills are disabled by enterprise policy, use the copy-and-paste prompts in [PROMPTS.md](PROMPTS.md).

Python 3 is optional for the Markdown instructions. Python 3 is required for the supplied validation and local-tool wrappers. The scripts use only the Python standard library.

## Connect the future `run-db-query` project

The database runner is intentionally a separate trusted project.

1. Build and start that service outside this repository.
2. Keep all database authentication inside that service.
3. Copy the generated local configuration if it does not exist:

```text
.agent/templates/LOCAL_TOOLING.example.json
    → .agent/local/LOCAL_TOOLING.json
```

4. Configure either:
   - `command`: an external executable or script that owns authentication; or
   - `rest`: a loopback HTTP endpoint such as `http://127.0.0.1:8765`.
5. Run **Tasks: Run Task → DB Tool: Doctor**.

Do not place a username, password, token, DSN, or connection string in the local configuration. The client rejects common credential fields.

The exact interface is in [.agent/DB_TOOL_CONTRACT.md](.agent/DB_TOOL_CONTRACT.md).

## Daily workflow

```text
Source file
   ↓
Local profile without sample values
   ↓
Candidate key hypotheses
   ↓
Reviewed bounded database experiments
   ↓
Unique / ambiguous / unmatched metrics
   ↓
Holdout validation
   ↓
Evidence-backed mapping or explicit unresolved result
```

Workmate coordinates the task. DB Scout runs only approved database experiments through `tools/dbtool.py`. Reviewer performs a read-only assessment. Librarian stages reusable learning under `.agent/local/pending/`; it cannot silently rewrite canonical instructions or skills.

## Main commands

Windows:

```bat
tools\agentctl.cmd init
tools\agentctl.cmd doctor
tools\agentctl.cmd status
tools\agentctl.cmd verify fast
tools\agentctl.cmd verify full
tools\dbtool.cmd doctor
```

macOS or Linux:

```sh
sh tools/agentctl.sh init
sh tools/agentctl.sh doctor
sh tools/agentctl.sh status
sh tools/agentctl.sh verify fast
sh tools/agentctl.sh verify full
sh tools/dbtool.sh doctor
```

## Layout

```text
AGENTS.md                              canonical operating and safety rules
.github/agents/                        Workmate, DB Scout, Reviewer, Librarian
.github/skills/                        task, reconciliation, DB, review, learning skills
.agent/templates/                      templates copied into private local state
.agent/local/                          ignored work state and results
.agent/DB_TOOL_CONTRACT.md             contract for the separate DB runner
.agent/TOOLBOX.md                      deterministic commands
.agent/harness.json                    verification configuration
.vscode/tasks.json                     ready-to-run VS Code tasks
tools/agentctl.py                      task and memory harness
tools/dbtool.py                        bounded client for the external DB runner
tools/safety_scan.py                   public-repository leak check
```

## Capability fallback

Use the highest capability that the managed VS Code exposes:

| Available capability | Use |
|---|---|
| Copilot Chat only | Attach `AGENTS.md`, the relevant local state, and use `PROMPTS.md`. |
| Agent mode and terminal | Let Workmate run the supplied scripts with normal approvals. |
| Skills and custom agents | Select Workmate, DB Scout, Reviewer, or Librarian and invoke slash skills. |
| Subagents | Let Workmate delegate isolated review. |
| Approved MCP or hooks | Add deterministic policy enforcement later. The base project does not depend on them. |
