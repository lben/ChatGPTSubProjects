---
name: refine-experience
description: Review completed work and stage small evidence-supported proposals for local memory, decisions, toolbox entries, or sanitized Agent Skills. Use only after useful work or a corrected failure.
disable-model-invocation: true
argument-hint: '[completed task or failure]'
---

# Refine experience

This skill stages proposals. It does not directly change canonical knowledge.

Create `.agent/local/pending/YYYYMMDD-HHMMSS-short-name.md` only when evidence supports a recurring procedure, stable preference, verified defense, durable fact, reliable command, or long-lived decision.

Choose one destination:

- local memory;
- local decisions;
- tracked toolbox;
- tracked sanitized skill;
- no destination for temporary, sensitive, speculative, or unsupported information.

A proposal must include trigger, scope, evidence, duplicate and contradiction checks, exact patch, security review, validation, rollback, and revisit condition.

Never include company names, file paths, schema names, table names, column names, SQL, values, rows, credentials, or connection information in a tracked proposal. `Nothing worth saving` is valid.

Promotion requires explicit user approval. Then run validation, relevant verification, the security scan, and inspect the Git diff.
