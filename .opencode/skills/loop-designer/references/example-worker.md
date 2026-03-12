# Example Worker Skill — Test Coverage Optimizer

This is a reference example showing what a finished worker skill looks like. It follows the `loop-template.md` structure exactly. Use it to calibrate the shape, specificity, and decision-rule density of the workers you design.

This worker operates in a different domain (code quality) than the content/marketing examples in the main skill — intentionally, so you don't over-anchor on one domain shape.

```md
---
name: test-coverage-optimizer
description: Increase test coverage of critical paths to 80% while keeping the test suite fast and maintainable.
version: 1.0
---

# Test Coverage Optimizer

## Mission
- North star: fewer production regressions per release
- Operational objective: increase branch coverage of critical modules from 45% to 80%
- Stop condition: all critical modules reach 80% branch coverage, or 20 cycles with no coverage gain

## Operational Score
- Primary score: branch coverage % across critical modules
- Direction: higher is better
- Review cadence: per cycle (each cycle = one test-writing session)
- Leading indicators: number of untested branches in critical paths, test execution time

## Verification Surface
| What to check | How to check | Good looks like | Cadence |
| --- | --- | --- | --- |
| Branch coverage % | `npx vitest --coverage` | >= previous cycle | every cycle |
| Test execution time | `time npx vitest` | < 60 seconds total | every cycle |
| Tests passing | `npx vitest --run` | 0 failures | every cycle |
| No flaky tests | run suite 3x, compare results | identical results | every 5 cycles |

## Environment

### Action-to-Tool Map
| Action | Tool / API | Access | Checkpoint | Verification source |
| --- | --- | --- | --- | --- |
| Read coverage report | vitest coverage JSON output | ready | autonomous | coverage/coverage-summary.json |
| Identify untested branches | coverage report + source analysis | ready | autonomous | uncovered line numbers in report |
| Write test files | file write tools | ready | autonomous | test file exists and passes |
| Run test suite | bash: npx vitest | ready | autonomous | exit code 0 |
| Commit changes | bash: git commit | ready | human-approval | human reviews test quality before merge |

### Permissions
- Read/write access to `src/` and `tests/` directories
- Git commit access (human approves merge)

### Off-limits
- Do not modify source code to make it easier to test — test the code as it is
- Do not delete or weaken existing tests
- Do not add test dependencies without human approval

### Inputs
| Input | Source | Quota / Limit | Legal constraint | If exhausted |
| --- | --- | --- | --- | --- |
| Source files | local repo | n/a | n/a | n/a |
| Coverage data | vitest output | n/a | n/a | n/a |

## On Start

1. Read `results.jsonl` — understand which modules have been covered and what approaches worked
2. Read `playbook.md` — current best strategy for writing effective tests
3. Run `npx vitest --coverage` — get current coverage baseline
4. Pick the next uncovered critical module from the coverage report

## Operating Principles

- One module per cycle. Write tests for one module, verify, record. Don't scatter across files.
- Prioritize by risk, not by ease. Cover the module most likely to cause a production regression first, not the one easiest to test.
- Prefer integration tests over unit tests when the module's value is in how it connects to other modules.
- Simplicity criterion: if a simpler test achieves the same coverage, prefer it. Removing a complex test and replacing it with a simpler one that maintains coverage = a win.
- Never mock what you can use directly. Mocks that drift from real behavior create false confidence.
- If test execution time exceeds 60 seconds, stop adding tests and optimize the slow ones first.

## Work Loop

1. Run coverage report, compare to baseline
2. Identify the critical module with lowest branch coverage
3. Read the module source, understand the branching logic
4. Write tests targeting uncovered branches — one test file per module
5. Run the full test suite — confirm all tests pass and no existing tests broke
6. Run coverage report — measure the delta
7. Record result in `results.jsonl`
8. If coverage improved and tests are clean: keep. If coverage didn't improve or tests are flaky: discard and try a different approach.
9. Update `playbook.md` if a new testing pattern proved effective
10. Repeat from step 1

### Stall Rule
If coverage has not improved for 3 consecutive cycles: stop writing new tests. Instead, review the experiment log for patterns — are the remaining uncovered branches genuinely untestable (dead code, error paths that require external failures)? If yes, flag them for human review and move to the next module. If no, try a fundamentally different testing approach (e.g., switch from unit to integration tests).

## Diagnostic Matrix

| Coverage delta | Test time delta | Diagnosis | Action |
| --- | --- | --- | --- |
| Positive | Stable | Working — continue | Keep tests, move to next module |
| Positive | Increased significantly | Tests are expensive | Keep tests but optimize before next cycle |
| Zero | Any | Tests aren't reaching new branches | Rethink approach — different test strategy |
| Negative | Any | Broke something | Discard immediately, investigate |

## Memory
- Results log: `results.jsonl`
- Best-known playbook: `playbook.md`
- Next cycle reads first: `results.jsonl`

Each log entry is one JSON object per line (JSONL):
`{"id": "cycle-003", "date": "2025-01-15", "module": "src/auth/session.ts", "action": "wrote integration tests for token refresh branches", "coverage_before": 45.2, "coverage_after": 52.1, "score_delta": 6.9, "test_time_ms": 42000, "status": "keep", "reasoning": "Integration test hit 3 previously uncovered error branches. Test time still under 60s."}`

## Safety
- Hard stops: never modify source code, never delete existing tests, never add dependencies
- Budget limits: max 10 test files per cycle, max 60s total test execution time
- Escalation triggers: 3 consecutive cycles with no improvement → pause and flag for human review

## Closed Loop Test
- [x] Can observe the relevant world state (coverage report)
- [x] Can act on the environment (write test files)
- [x] Can verify whether the action helped (re-run coverage)
- [x] Can record what happened for the next cycle (results.jsonl)
- [x] Can continue autonomously without human judgment (next module is auto-selected from coverage report)

## Proof of Loop
- Cycle 0: run `npx vitest --coverage`, record baseline coverage per module. Change nothing.
- Cycle 1: pick lowest-coverage critical module, write one test file targeting uncovered branches, re-run coverage, record delta.
- Expected proof: coverage for the target module increases, all existing tests still pass, test time stays under 60s.
```
