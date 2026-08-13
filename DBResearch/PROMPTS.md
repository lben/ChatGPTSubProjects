# Manual prompt fallback

Use these prompts when custom agents, Agent Skills, or prompt files are unavailable.

## Start or resume

```text
Follow AGENTS.md. Run tools\\agentctl.cmd init if local state is absent. Read .agent/local/ACTIVE_TASK.md, .agent/local/MEMORY.md, .agent/TOOLBOX.md, and only relevant decisions and skills. Resume the active task. If empty, convert my request into Core goal, Done when, Non-goals, and Real proof. Keep all company-specific information under .agent/local/. Inspect before editing. Complete the smallest safe milestone, verify real behavior, update local state, and report outcome, evidence, risk, and required action.

My request: <TASK>
```

## Reconcile data

```text
Follow AGENTS.md and .github/skills/reconcile-data/SKILL.md. Initialize local state. Profile this source without placing sample values in chat or tracked files. Identify candidate source keys. Search database metadata first. Create one bounded reviewed experiment at a time under .agent/local/db-requests/. Use only tools\\dbtool.cmd through the run-db-query procedure. Measure unique, ambiguous, unmatched, null-loss, and duplicate results. Validate the final candidate on a deterministic holdout. Update .agent/local/RECONCILIATION.md.

Source and objective: <SOURCE AND OBJECTIVE>
```

## Independent review

```text
Act as a read-only reviewer. Follow AGENTS.md and verify-change. Review the active local task, reconciliation ledger, changed files, and evidence. Check credential and company-data exposure, candidate validity, ambiguous matches, holdout independence, acceptance coverage, correctness, unnecessary scope, and weak proof. Return findings by severity, then a pass/fail/unverified verdict per criterion.
```

## Refine experience

```text
Follow refine-experience. Review completed work and evidence. Write proposals only under .agent/local/pending/. Do not change canonical tracked files. Generalize and remove all company-specific identifiers, SQL, values, rows, paths, and credentials. Say Nothing worth saving when there is no durable signal.
```
