---
name: verify-change
description: Verify a change or reconciliation conclusion against explicit acceptance criteria with layered executable evidence and independent review. Use before declaring completion.
argument-hint: '[fast|full|criterion]'
---

# Verify change

For every `Done when` item, record proof method, command or observation, actual result, and limitation.

Use only relevant layers:

1. static validation;
2. compilation or type checking;
3. focused behavior tests;
4. integration tests;
5. end-to-end acceptance;
6. operational checks such as permissions, limits, performance, and rollback;
7. reconciliation holdout evidence.

Reject completion when a criterion lacks evidence, tests only assert implementation choices, tests were weakened, an assumption is unverified, ambiguous matches are hidden, holdout data was reused for tuning, or reported evidence differs from tool output.

Reviewer returns findings first, then a pass, fail, or unverified verdict for each criterion.
