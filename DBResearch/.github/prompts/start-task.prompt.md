---
name: start-task
description: Start or resume a DBResearch task with private state and explicit proof.
agent: Workmate
argument-hint: '[task or outcome]'
---

Follow [AGENTS.md](../../AGENTS.md) and [task-cycle](../skills/task-cycle/SKILL.md).

Initialize local state when needed. Resume the active task. If it is empty, create a task contract from:

${input:task:Describe the required outcome}

Keep work-specific information under `.agent/local/`. Verify real behavior and report only result, evidence, risk, and required action.
