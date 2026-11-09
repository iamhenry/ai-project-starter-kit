export const meta = {
  name: "hivecall-retro",
  description: "Judge every hivecall run of the week on the same fixed stages, then name what is systemically going well or wrong",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      // Thread ids to judge; default: every archived thread that loaded hivecall, archived in the last `days` days.
      runs: { type: "array", items: { type: "string" } },
      days: { type: "integer", minimum: 1, maximum: 60 },
      // Post the report as a GitHub issue; false returns it only.
      post: { type: "boolean" },
    },
  },
  phases: [
    { title: "Find", detail: "Archived threads that loaded hivecall this week" },
    { title: "Judge", detail: "Four judges per run, every stage answered with evidence" },
    { title: "Synthesize", detail: "Patterns across runs and weeks, up to three fixes, draft issue" },
  ],
};

// The stage list is the contract; definitions live in the profile so they are written once.
const PROFILE = ".agents/skills/retro/references/hivecall/hivecall.md";
const GROUPS = {
  Setup: ["kickoff", "plan"],
  Work: ["handoff", "build", "review"],
  Proof: ["proof", "stuck", "keep-working"],
  Oversight: ["watchdog", "owner-channel", "close"],
};
// Judges: openai/gpt-6-luna at xhigh. Synthesis: anthropic/claude-opus-5-5 at medium (set literally in each call).
const ISSUE_TITLE = "[Draft proposal] Hivecall retro";

const input = args && typeof args === "object" ? args : {};
const days = Number.isInteger(input.days) ? input.days : 7;
const post = input.post !== false;

const cellSchema = {
  type: "object",
  required: ["status", "evidence"],
  additionalProperties: false,
  properties: { status: { enum: ["PASS", "FAIL", "UNKNOWN"] }, evidence: { type: "string", minLength: 8 } },
};
const groupSchema = (stages) => ({
  type: "object",
  required: stages,
  additionalProperties: false,
  properties: Object.fromEntries(stages.map((stage) => [stage, cellSchema])),
});

phase("Find");
// A run is a BB thread that loaded the hivecall skill; its saved folder (if any) adds the plugin's records.
let runs = Array.isArray(input.runs) ? input.runs.map((thread) => ({ thread, folder: "" })) : null;
if (!runs) {
  const found = await agent(
    `Find every finished hivecall run: archived threads only, in all projects, archived in the last ${days} days. Active threads may still be working, so never include them.
1. List threads: \`bb thread list --archived --json > <tmp>/archived.json\`; keep threads whose archivedAt is within the window.
2. For each, save \`bb thread log <id> --json --all > <tmp file>\` and keep it only if it has a completed \`skill\` tool call whose name argument is exactly \`hivecall\`. Titles, mentions and claims do not count. Also drop threads whose log never writes a run card (\`.hivecall/run.md\`): they discussed hivecall but ran nothing.
3. For each kept thread, folder = the directory under ~/.hivecall/runs/*/ whose name ends with that thread id, or "" if none.
If \`bb\` fails on a stale BB_CLI, run \`env -u BB_CLI bb ...\`. Do not read run contents beyond this.`,
    { provider: "opencode", model: "openai/gpt-6-luna", reasoningLevel: "medium", label: "Find runs", phase: "Find",
      schema: { type: "object", required: ["runs"], additionalProperties: false, properties: { runs: { type: "array", items: {
        type: "object", required: ["thread", "folder"], additionalProperties: false,
        properties: { thread: { type: "string" }, folder: { type: "string" } } } } } } },
  );
  runs = found?.runs ?? [];
}
log(`${runs.length} run(s) to judge`);

phase("Judge");
const judgePrompt = (run, group, stages) => `You judge one hivecall run on fixed stages. Read ${PROFILE} first: its "Where the evidence is" and the "${group}" stages are your contract.

Orchestrator thread: ${run.thread}
Saved run folder: ${run.folder || "none (read the thread log and its worktree if it still exists)"}
Stages: ${stages.join(", ")}

Rules:
- Answer every stage with PASS, FAIL or UNKNOWN and one evidence line (file and line, event time, or log sequence). PASS needs evidence too.
- Read the records, not the orchestrator's claims about them. Save large logs to a temp file and search them; never sample.
- UNKNOWN only after you tried; say what you tried.
- Do not edit any file. Do not quote the owner; paraphrase.`;

const grids = [];
for (const run of runs) {
  const entries = Object.entries(GROUPS);
  const answers = await parallel(entries.map(([group, stages]) => () => agent(judgePrompt(run, group, stages), {
    provider: "opencode", model: "openai/gpt-6-luna", reasoningLevel: "xhigh", label: `${run.thread} · ${group}`, phase: "Judge", schema: groupSchema(stages),
  })));
  const grid = {};
  entries.forEach(([group, stages], index) => {
    for (const stage of stages) {
      const cell = answers[index]?.[stage];
      // A missing or empty cell fails the workflow: no report may be half done.
      if (!cell || !["PASS", "FAIL", "UNKNOWN"].includes(cell.status) || !cell.evidence)
        throw new Error(`Judge ${group} left stage ${stage} unanswered for ${run.thread}`);
      grid[stage] = cell;
    }
  });
  grids.push({ thread: run.thread, folder: run.folder, grid });
}

phase("Synthesize");
const report = await agent(`You write the weekly hivecall retro from fixed stage grids. Read ${PROFILE} ("Goal", "Privacy", "Proposed fixes").

Grids (one per run, every stage judged with evidence):
${JSON.stringify(grids, null, 2)}

Past weeks: read the last four GitHub issues titled "${ISSUE_TITLE}" on iamhenry/ai-project-starter-kit (gh issue list --search, gh issue view) and compare their grids with this week's.

Write a Markdown report:
1. Two or three sentences: what is systemically going well and what is going wrong.
2. A table: one row per run (thread title, project, goal in a few words), one column per stage, PASS/FAIL/UNKNOWN.
3. For each FAIL: one line with its evidence. Verify the evidence for each FAIL yourself before keeping it.
4. Trend versus past weeks: which stages improved or got worse, and which recent harness change (git log -- .opencode/plugins/hivecall) likely explains it.
5. Up to three proposed fixes, per the profile.
Apply the profile's privacy rules. Do not edit files or commit.${post ? `

Then post the report as a new GitHub issue titled "${ISSUE_TITLE} - <M/D/YY>" (today's local date) on iamhenry/ai-project-starter-kit, or update this week's issue if it exists. If no runs were judged, post nothing.` : ""}`,
  { provider: "opencode", model: "anthropic/claude-opus-5-5", reasoningLevel: "medium", label: "Synthesis", phase: "Synthesize",
    schema: { type: "object", required: ["markdown", "issueUrl"], additionalProperties: false,
      properties: { markdown: { type: "string" }, issueUrl: { type: "string" } } } },
);

return { runs: grids.length, grids, report: report?.markdown ?? "", issueUrl: report?.issueUrl ?? "" };
