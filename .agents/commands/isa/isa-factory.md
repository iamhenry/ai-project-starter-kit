---
name: isa-factory
description: Run the local ISA Factory against one authoritative ISA path.
agent: orchestrator
subtask: false
---

# ISA Factory

Thin entrypoint. The complete workflow lives in `isa-factory`.

## Invoke

1. Require exactly one `$ARGUMENTS` value: an ISA path or one `@file` reference.
2. Resolve `@file` to its path, reject zero or multiple values, and do not use a default path.
3. Load `.agents/skills/isa-factory/factory/SKILL.md`.
4. Pass the resolved path, activate Authoritative Artifact Mode, and execute the skill end to end.

Usage: `/isa-factory @_ai/docs/ISA.md`
