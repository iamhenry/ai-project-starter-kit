---
description: Clarify a whole app into one behavior-first Product ISA, ready for direct implementation.
agent: build
subtask: false
---

# Product ISA

Thin entrypoint. The complete workflow lives in the `product-isa` skill.

## Invoke

1. Load `.opencode/skills/product-isa/SKILL.md`.
2. Pass the product idea and any input paths from `$ARGUMENTS`.
3. Execute the skill end to end; do not recreate or expand its workflow here.

**Output:** `_ai/docs/ISA.md`

This is an isolated experiment. Do not modify or invoke the existing product ADR, technical ADR, or roadmap workflow unless the user explicitly asks.
