---
name: minimal-correct-code
description: Produce the smallest complete, maintainable, and secure code change without speculative architecture or tests for imagined behavior. Use for implementation, refactoring, bug fixing, and code review.
user-invocable: false
---

# Minimal correct code

1. Define observable acceptance criteria.
2. Inspect existing architecture and reuse its patterns.
3. Prefer existing functionality, existing vetted dependencies, the standard library, then a small local implementation.
4. Do not add future architecture, generic frameworks, compatibility layers, switches, fallbacks, or abstractions unless required now.
5. Keep comments for non-obvious intent, invariants, risk, or external constraints.
6. Validate inputs at real boundaries.
7. Preserve explicit contracts and type safety.
8. Test real behavior and important failure modes.
9. Prefer an executable acceptance check when practical.
10. Remove accidental complexity before completion.

A small patch is not better when incomplete or unsafe. A large patch is not better because it anticipates hypothetical needs.
