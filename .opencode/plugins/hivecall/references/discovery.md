# Discovery route

Use this before drafting the normal goal contract when the input cannot yet support a falsifiable check for every Verification line, such as an ambiguous goal or raw bug report. The owner does not approve the discovery contract or plan: their kickoff answers authorize the run, and judges decide competing approaches and plan readiness when there is a real plan; a planless non-bug finding also needs a reviewer verdict, even for one option. Choose the route per item; discovery depth scales with the evidence.

## Discovery ledger

Adapt this template under a `Discovery` heading to the unknowns that need resolving, using the normal ledger format; omit unneeded items, including the plan item for a simple evidence-backed finding. IDs shown (`ISC-1`–`ISC-3`) are defaults; if the ledger already has items, use the next free ISC numbers, and number implementation items after the discovery items.

```html
<h3>Discovery</h3>
<ul class="isc">
<li id="ISC-1"><input type="checkbox" disabled> ISC-1: context gathered and bug symptom reproduced where applicable — check: bugs: reproduction result says REPRODUCED (qa may reply PASS) at the reported entry point and gather-context evidence exists; non-bugs: fresh reviewer SELECTED on cited finding/evidence file</li>
<li id="ISC-2"><input type="checkbox" disabled> ISC-2: cause proven or requirement resolved — check: fresh qa REPRODUCED or PASS confirms the reproduction/cause with cited evidence, or fresh reviewer SELECTED confirms a cited non-bug finding</li>
<li id="ISC-3"><input type="checkbox" disabled> ISC-3: implementation plan approved — check: plan.md Plan Judge section says APPROVE_PLAN</li>
</ul>
```

- Reuse an existing ticket or create one with `create-ticket`; skip ticket creation when the user supplied a goal, spec, or ISA.
- Keep `ticket.md`, `issue.md`, `research/`, `plan.md`, and reproduction evidence in `_ai/task/{YYYY-MM-DD}/{slug}/` as their owners declare. Keep only the ledger and run card in `.hivecall/`; do not duplicate artifacts.
- For bugs, run `reproduce-bug` via a fresh `qa` first. Continue only on `REPRODUCED` evidence (qa may reply `PASS` on this check) from the reported entry point, then run `gather-context` for local code and official external docs. Non-bug tasks skip reproduction and resolve requirements/unknowns with cited evidence.
- Prove the cause before planning; name `bugging-out` when it is unclear. Only the orchestrator ticks discovery items, under the normal ledger rules, from a fresh independent verdict with a receipt.
- If two or more supported approaches remain after the cause item, run `judge-proposal` via a fresh `reviewer` before planning. For a planless non-bug finding, also use `judge-proposal` on the cited finding/evidence file even with one option, to obtain `SELECTED`.
- When a real plan is needed, create `plan.md` with `.agents/commands/workflow/01-plan/02-create-issue.md`, then run `judge-plan` via a fresh `reviewer`. Allow at most two plan revisions; after the second, park the plan item with its unlock condition.
- A judge's `ASK_USER` means one `🚦` question; park that item and continue other work. Do not ask the owner to approve the discovery contract or plan.
- Evidence is scriptable: the reproduction result file contains its verdict, the cause write-up cites evidence paths, and, when a plan exists, its `Plan Judge` section says `APPROVE_PLAN`.
- On either route, append the vetted implementation items in the same ledger edit that ticks the last discovery item, or the watchdog sees a complete ledger and pauses. If a plan exists, convert it to the goal contract on `APPROVE_PLAN`. Use reproduction steps as the contract's E2E smoke for before/after proof.
- Start the watchdog at kickoff when selected; discovery needs no watchdog changes. Research and judge briefs use `PROMISE: kind=helper`.

- A simple finding can proceed without `plan.md` or `judge-plan`, but still needs a fresh qa `REPRODUCED` (or `PASS` on the item's check) for a reproduction/cause, or a fresh reviewer `SELECTED` on the cited finding/evidence file for a non-bug finding. Cited research alone never ticks. Include the discovery item in the helper’s valid PROMISE rows and attach the normal receipt. The implementation item needs a falsifiable check and real-entry-point E2E smoke before build. For every find-out item, a negative result (NOT_REPRODUCED, BLOCKED, FAIL, no cause/source found) never ticks or proves absence. Give one fresh helper what was tried and retry with one changed angle (entry point, setup, data or steps); if still negative, park and ask one 🚦 question listing tried and needed, then continue other work.
