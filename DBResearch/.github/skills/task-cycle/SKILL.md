---
name: task-cycle
description: Start, resume, execute, verify, and close non-trivial repository work with explicit acceptance criteria and private resumable state. Use for features, fixes, investigations, and operational tasks.
argument-hint: '[task or outcome]'
---

# Task cycle

## Start

1. Read `AGENTS.md`.
2. Run `agentctl init` when local state is absent.
3. Read `.agent/local/ACTIVE_TASK.md`, `.agent/local/MEMORY.md`, and `.agent/TOOLBOX.md`.
4. Read only relevant local decisions and skills.
5. Reconcile a new request with existing active work. Do not silently abandon a task.
6. Define Core goal, Done when, Non-goals, and Real proof.
7. Record the smallest complete milestone and exact next action.

## Inspect

- Locate existing behavior, conventions, commands, and tests.
- Identify the narrowest safe change.
- Prefer deterministic evidence.
- Keep company-specific state under `.agent/local/`.

## Execute

- Use existing commands and APIs first.
- Change the fewest files needed for a complete result.
- Preserve unrelated behavior.
- Update resumable local state after a material transition.

## Verify

- Run focused checks while iterating.
- Run the full tier before completion.
- Map evidence to every criterion.
- Test observable behavior, not only syntax.

## Review and close

Use Reviewer for material work. Mark `DONE` only with sufficient evidence. Invoke `refine-experience` manually. Archive only after acceptance when acceptance is required.
