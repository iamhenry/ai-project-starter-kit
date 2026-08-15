# Review Verdict Output Template

Use this format when the task is analysis-only (validation/review/investigation) and no implementation was requested.

---

## Context Summary

**Task type:** Analysis-only
**What was checked:** [1-2 lines]
**Constraints:** [Scope limits and what was not changed]
**Blast radius overview:** [Areas potentially impacted]

---

## Claim Verdicts

### Claim 1 — [short claim text]
**Verdict:** Valid | Invalid | Unclear
**Evidence:**
- `path/to/file.ext:line` - [what this proves]
- `path/to/file.ext:line` - [what this proves]
**Blast radius:** [who/what is affected if true]
**Confidence:** High | Medium | Low - [one-line rationale]

---

### Claim 2 — [short claim text]
**Verdict:** Valid | Invalid | Unclear
**Evidence:**
- `path/to/file.ext:line` - [what this proves]
- `path/to/file.ext:line` - [what this proves]
**Blast radius:** [who/what is affected if true]
**Confidence:** High | Medium | Low - [one-line rationale]

---

## Gaps / Missing Evidence

- [Only include if any verdict is Unclear]
- [State exactly what is missing to resolve]
