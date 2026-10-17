# Hivecall proposal gate

This gate judges one proposed hivecall-skill change before it is applied. It is
not the replay evaluation or release gate: a PASS only means the proposal is
worth evaluating. A change ships only after it beats the baseline and meets the
weekly eval's other criteria.

## Input

The runner accepts one UTF-8 JSON object with these fields:

```json
{
  "target_behaviors": ["3. Never goes quiet while work is open"],
  "owning_file": ".agents/skills/hivecall/SKILL.md",
  "proposed_edit": "Exact diff or exact insertion/replacement text",
  "verification": "A falsifiable check of the claimed behavior change",
  "trace_evidence": {
    "source": "BB thread log or measured aggregate",
    "thread_id": "thr_example",
    "moment": "Date and time range, or count window",
    "observations": "Concrete events, counts, or spot-checks establishing the gap"
  },
  "cause_class": "execution_drift"
}
```

`owning_file` names the primary owner. If a complete fix must synchronize
dependent instructions, include every exact change in `proposed_edit` and keep
the primary ownership rationale explicit.

Use the seven ranked behaviors from the weekly eval: (1) finish every item or
park it with a reason; (2) every tick has proof; (3) never go quiet while work
is open; (4) parallelize without clashes; (5) watchdog alerts only on real
problems and never misses a real stall; (6) workers get clear bounded tasks and
report cleanly; (7) finish in reasonable time and cost. The cause class must be
one of `artifact_gap`, `execution_drift`, `input`, `environment`, `wrong_owner`,
`one_off`, or `bloat`.

Verification must state an observable outcome and a check. Evidence must name
its source and moment and state the concrete event/count.
"No failure observed" is not evidence for a change. A thread ID or a model's
assertion alone is not evidence. Never include secrets, personal data, or home
paths. The runner redacts the complete judge payload locally before sending any
proposal text to a model; use `--preview` to inspect that redacted payload.

## Judgment

Use the four questions in [the retro's existing "Before proposing a change"
section](../../issue-to-pr/issue-to-pr.md#before-proposing-a-change): what exact
evidence shows the gap and what is unknown; whether an existing instruction
already covers it; which artifact owns it and whether it generalizes; and the
smallest useful change and guarantees that must survive. Execution drift alone
does not justify another rule; an enforcement change must name the specific
failure it prevents.

Reuse the hard gates, weighted rubric, and 80-point decision threshold from the
[judge-proposal skill](../../../../../skills/judge-proposal/SKILL.md). Reject before
scoring if any hard gate fails. In addition, reject if the proposal is not tied
to a real observed failure, targets the wrong owning file, introduces a new
mechanism where a smaller existing-file edit works, or breaks an invariant.
Otherwise PASS only if every hard gate passes and the weighted score is at least
80/100. Give a concise, evidence-based reason for every rejection and explain
any unsupported claim.

The live authority is the current hivecall skill plus
[HOW-TO-WORK.md](../../../../hivecall/HOW-TO-WORK.md); do not weaken or contradict any of its
owner invariants. Also preserve these weekly-loop invariants:

1. Every claim traces to a log event, count, or spot-check.
2. Missing evidence never improves a score.
3. A weak score produces a proposal or a stated reason for none.
4. A change ships only if it beats baseline and passes this gate.
5. The process is read-only toward threads.
6. No secrets or private data leave the machine or reach an issue or PR.

## Artifact ownership hints

Use the artifact that owns the behavior, not the retro tooling that observed
it. The hivecall `SKILL.md` owns orchestration and delegation rules;
`HOW-TO-WORK.md` owns run-wide constants and invariants; `references/kickoff.md`
owns kickoff questions and setup; `watchdog/` owns watchdog detection and
alerting. The retro reference owns trace collection and analysis, not the
runtime behavior of a hivecall run. If evidence or ownership is unclear, reject
with the specific gap rather than guessing.

## Output

Return exactly one JSON object, with no Markdown fence or other text:

```json
{
  "verdict": "PASS",
  "score": 86,
  "reasons": ["The trace shows ...", "The one-file edit ..."],
  "hard_gate_failures": [],
  "rubric_scores": {
    "acceptance_fit": 22,
    "evidence_fit": 18,
    "ethos_fit": 14,
    "reuse_style_fit": 11,
    "blast_radius": 9,
    "verification_clarity": 8,
    "phase_fit": 4
  }
}
```

Use `REJECT` when a hard gate fails or the score is below 80. A rejected
proposal may have `score: null` and an empty `rubric_scores` object when a hard
gate rejects it before scoring. The weights are 25/20/15/15/10/10/5 in the
field order shown. The runner validates the JSON shape and writes one verdict
file for the weekly eval to consume.

Run it from the repository root with:

```sh
python3 .agents/skills/retro/references/hivecall/gate/run-gate.py \
  --proposal .lanes/proposal.json \
  --output .hivecall/verification/gate-result.json
```

The default judge is `kimi-k3` on Ollama Cloud. The runner sends only the locally
redacted prompt through the direct chat API; it does not attach agent context or
tools. `--model` accepts another non-GPT Ollama model. Malformed output gets one
retry; each raw reply is saved locally after redaction beside the verdict, and a
second malformed reply writes an `ERROR` verdict rather than `PASS`.
