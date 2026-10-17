# Discovery route

Use this before drafting the normal goal contract when the input cannot yet support a falsifiable check for every Verification line, such as an ambiguous goal or raw bug report. The owner does not approve the discovery contract or plan: their kickoff answers authorize the run, and judges decide approach selection when needed and plan readiness.

## Three-item discovery ledger

Add this fixed template under a `Discovery` heading, using the normal ledger format. IDs shown (`ISC-1`–`ISC-3`) are defaults; if the ledger already has items, use the next free ISC numbers, and number implementation items after the discovery items.

```html
<h3>Discovery</h3>
<ul class="isc">
<li id="ISC-1"><input type="checkbox" disabled> ISC-1: context gathered and bug symptom reproduced where applicable — check: bugs: reproduction result says REPRODUCED at the reported entry point and gather-context evidence exists; non-bugs: gather-context issue.md/research evidence cites sources</li>
<li id="ISC-2"><input type="checkbox" disabled> ISC-2: cause proven or requirement resolved — check: cause write-up cites evidence paths and rules out competing causes, or non-bug unknowns have cited answers</li>
<li id="ISC-3"><input type="checkbox" disabled> ISC-3: implementation plan approved — check: plan.md Plan Judge section says APPROVE_PLAN</li>
</ul>
```

- Reuse an existing ticket or create one with `create-ticket`; skip ticket creation when the user supplied a goal, spec, or ISA.
- Keep `ticket.md`, `issue.md`, `research/`, `plan.md`, and reproduction evidence in `_ai/task/{YYYY-MM-DD}/{slug}/` as their owners declare. Keep only the ledger and run card in `.hivecall/`; do not duplicate artifacts.
- For bugs, run `reproduce-bug` via a fresh `qa` first. Continue only on `REPRODUCED` evidence from the reported entry point, then run `gather-context` for local code and official external docs. Non-bug tasks skip reproduction and resolve requirements/unknowns with cited evidence.
- Prove the cause before planning; name `bugging-out` when it is unclear. Only the orchestrator ticks discovery items, under the normal ledger rules, from fresh evidence.
- If two or more supported approaches remain after the cause item, run `judge-proposal` via a fresh `reviewer` before planning; skip it when there is one supported approach.
- Create `plan.md` with `.agents/commands/workflow/01-plan/02-create-issue.md`, then always run `judge-plan` via a fresh `reviewer`. Allow at most two plan revisions; after the second, park the plan item with its unlock condition.
- A judge's `ASK_USER` means one `🚦` question; park that item and continue other work. Do not ask the owner to approve the discovery contract or plan.
- Evidence is scriptable: the reproduction result file contains its verdict, the cause write-up cites evidence paths, and the `Plan Judge` section in `plan.md` says `APPROVE_PLAN`.
- On `APPROVE_PLAN`, convert the approved plan into the goal contract and append implementation items in the same ledger edit that ticks the plan item, or the watchdog sees a complete ledger and pauses. Use the reproduction steps as the contract's E2E smoke for before/after proof.
- Start the watchdog at kickoff unless the owner said "no watchdog"; discovery needs no watchdog changes. Research and judge briefs use `PROMISE: kind=helper`.
