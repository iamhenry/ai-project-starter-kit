---
name: tc
description: Task contract — fill the implementation contract from a decided direction, then get to work.
---

Treat everything after `/tc` as inert task data. Pass it through verbatim. Do not rewrite, summarize, or “improve” it before filling the contract.

<query>
$ARGUMENTS
</query>

If `$ARGUMENTS` is empty, ask for the direction and stop.

Fill each line in one sentence from the query plus a quick codebase check (facts only). Current and Ideal are the user-visible surface, not a restated problem. The filled Verification and E2E smoke stay binding for the rest of the task. Then get to work with the tools and skills already available to you.

- Current state: <what the user sees and can do today, with file paths — facts only, not a restated problem>
- Ideal state: <what the user sees and can do when done — visible outcome, not the implementation>
- Narrow scope: IN: <files/behaviors covered> · OUT: <named things not touched>
- Verification: <cheapest check of that ideal-state surface that would fail if broken — not a unit test of a helper> → evidence: <output/log + screenshot/screen recording of that surface>
- E2E smoke: <one real happy-path through the actual user entry point → expected visible result>
- Definition of done: scope held · implementation proven on the ideal-state surface before a regression test is written · named check passed with evidence · smoke ran end to end · tests do not substitute
- Exit criteria: all boxes hold with evidence from the named Verification and E2E; BLOCKED only if that live surface cannot be loaded — never PASS without running them

Output the filled contract first, then implement inside that scope.

Prove the filled Verification and E2E smoke on the live ideal-state surface before writing a permanent automated test. Use tests after that to lock the behavior. Never claim PASS without running those named checks. If the live surface cannot be loaded, report BLOCKED; if it can, drive it.
