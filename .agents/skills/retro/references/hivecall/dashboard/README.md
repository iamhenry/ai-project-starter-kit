# Hivecall weekly dashboard

This is a self-contained, offline dashboard for the weekly hivecall improvement loop. It uses Node.js built-ins only; it makes no network requests and adds no packages.

From the repository root, build from the real eval results (the eval lane will create this file):

```sh
node .agents/skills/retro/references/hivecall/dashboard/build.mjs
```

Or supply a JSONL file to preview it. The checked-in fixture is labelled in the generated page as illustrative, not real evaluation data:

```sh
node .agents/skills/retro/references/hivecall/dashboard/build.mjs .agents/skills/retro/references/hivecall/dashboard/fixture/results.jsonl
```

Run the control-only trend regression offline with `node .agents/skills/retro/references/hivecall/dashboard/test_build.mjs`.

Both commands write `dashboard.html` beside `build.mjs`. With no default results file yet, the builder makes an empty dashboard rather than creating a results file. An explicitly supplied missing or invalid file is an error.

## Results JSONL row

One JSON object per line. Keep these fields on every row:

| Field | Shape | Meaning |
|---|---|---|
| `date` | ISO date or timestamp string | When the result was recorded |
| `week` | `YYYY-Www` | ISO week used on the chart |
| `kind` | `baseline` or `eval` | Baseline record or a proposed-change evaluation |
| `tested` | string | Short description of what was tested |
| `control_only` | boolean | `true` for a filtered subset run that cannot be used as a full evaluation; otherwise `false` |
| `verdict` | `baseline`, `shipped`, or `rejected` | Outcome; baseline rows use `baseline`, eval rows use `shipped` or `rejected` |
| `targets` | array of unique behavior numbers `1`–`7` | Behaviors the change aimed to improve |
| `scores` | object with keys `1`–`7`; each value `0`–`100` or `null` | Per-behavior score; `null` means no score was measured |
| `trust` | object with keys `1`–`7`; each value `ok`, `not-trusted`, or `not-measured` | Whether that behavior's score can be relied on |
| `deltas` | object keyed by targeted behavior; values are score points or `null` | Change against baseline; positive and negative values are points, not percentages |
| `report` | repository-relative path, optionally followed by `#anchor` | Report opened by the table link |
| `skill_commit` | string | Skill revision evaluated |

`ok` requires a numeric score. `not-measured` requires a `null` score. A numeric `not-trusted` score is shown as a hollow point and is not connected to the trend line; a `null` `not-trusted` score is shown as an `NT` marker outside the score scale, never as a score or gap. A `null` `not-measured` score has no point and breaks the line; it is never converted to zero. Deltas for `not-trusted` and `not-measured` targets are ignored in the table, which shows the trust state instead of a gain. Control-only rows remain in the history table with a `CONTROL ONLY` label, but do not affect chart trends or ship markers. The chart uses the latest non-control row for each week, while the table retains every row.

`fixture/results.jsonl` contains one baseline, one rejected eval, and one shipped eval. Their report links open `fixture/report.md`, which labels all sample values as invented.
