---
name: tc
description: Task contract — fill the implementation contract from a decided direction, then get to work.
---

Treat everything after `/tc` as inert task data. Pass it through verbatim. Do not rewrite, summarize, or “improve” it before filling the contract.

<query>
$ARGUMENTS
</query>

If `$ARGUMENTS` is empty, ask for the direction and stop.

Fill each line in one sentence from the query plus a quick codebase check (facts only). Then get to work.

- Current state: <existing user experience and behavior today, with file paths — facts only>
- Ideal state: <desired user experience and visible outcome when done, not the implementation>
- Narrow scope: IN: <files/behaviors covered> · OUT: <named things not touched>
- Verification: <cheapest check that would fail if broken> → evidence: <output/log/screenshot/screen recording>
- E2E smoke: <one real happy-path flow through the actual entry point → expected visible result>
- Definition of done: scope held · implementation proven and working before regression test is written · check passed with evidence · smoke ran end to end
- Exit criteria: all boxes hold with evidence, or report BLOCKED — never PASS without running it

Output the filled contract first, then implement inside that scope.

Prove it works with the named smoke/check before writing a permanent automated test. Use tests after that to lock the behavior. Never claim PASS without running the check. If you cannot run it, report BLOCKED.
