# Agent readiness

An agent-ready project lets a new agent make a change, check it, and commit it
without guessing. Keep checks fast and make failures clear.

## Six rules

1. **One check:** `./check` runs the project checks. Aim for 10 seconds. Relax
   this only when project evidence supports a longer run.
2. **Every commit:** run `./check` before each commit.
3. **Use the stack tools:** check tests, lint and types with tools made for the
   project's language. A failed test or type check must fail `./check`.
4. **Ratchet rules:** warn first. Grandfather existing hits with a per-file
   ceiling and a reason. Only lower ceilings over time. Each rule states why it
   matters and how to fix it.
5. **Explain the checks:** `AGENTS.md` says how to run `./check` and names the
   check that enforces each repo rule.
6. **Keep each check in the right place:** `./check` enforces file-size limits
   with standard language linters. Secret scans, private detail checks and
   protected-file checks stay in the shared `.githooks/`.
   The size linter is required; `./check` fails if it is missing.

## Adopt

Copy the matching file from `templates/check/` to the project root as `./check`.
Also copy its linter config (`biome.json`, `.swiftlint.yml`, or `pylintrc`) to
the project root, then run `chmod +x ./check`. The shared pre-commit hook runs
this executable. Read its warnings and add project-specific checks only when
they help.

## Sources

- Henry's 21-repository survey (private notes).
- `chief-tui` `./check` and `checks/repo_rules.py` patterns.
- https://github.com/kodustech/agent-readiness
- https://factory.com/agent-readiness and https://factory.com/news/agent-readiness
- https://docs.grit.io/tutorials/gritql
- https://github.com/jayminwest/warren
- https://www.youtube.com/watch?v=aUNSTO6rED0
- https://x.com/sdrzn/status/2017732893024653682
