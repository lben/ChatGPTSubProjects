---
name: reconcile
description: Start or resume a source-file to database-key reconciliation.
agent: Workmate
argument-hint: '[source file and objective]'
---

Follow [reconcile-data](../skills/reconcile-data/SKILL.md).

Use local state only for company-specific information. Profile the source without exposing sample values. Rank source keys and database candidates. Use DB Scout for reviewed bounded experiments. Require unique-match and holdout evidence before accepting a mapping.

Objective:
${input:objective:Describe the source file and desired reconciliation}
