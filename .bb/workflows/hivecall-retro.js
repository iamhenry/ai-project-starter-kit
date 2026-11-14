export const meta = {
  name: "hivecall-retro",
  description: "Judge every eligible hivecall run in the window, summarize trends from KIT retro cards, and post only a checked report to KIT",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      runs: { type: "array", items: { type: "string" } },
      days: { type: "integer", minimum: 1, maximum: 60 },
      post: { type: "boolean" },
    },
  },
  outputSchema: {
    type: "object", required: ["runs", "grids", "report", "taskKey", "blocked"], additionalProperties: false,
    properties: {
      runs: { type: "integer" },
      grids: { type: "array", items: { type: "object" } }, report: { type: "string" },
      taskKey: { type: "string" }, blocked: { type: "array", items: { type: "object" } },
    },
  },
  phases: [
    { title: "Find", detail: "Archived threads that loaded hivecall this week" },
    { title: "Judge", detail: "Every eligible run in the window, with evidence for every stage" },
    { title: "Synthesize", detail: "Compare with past KIT retro cards and draft a private report" },
    { title: "Post", detail: "Scan the report before creating a KIT task card" },
  ],
};

const PROFILE = ".agents/skills/retro/references/hivecall/hivecall.md";
const GROUPS = {
  Setup: ["kickoff", "plan"],
  Work: ["handoff", "build", "review"],
  Proof: ["proof", "stuck", "keep-working"],
  Oversight: ["watchdog", "owner-channel", "close"],
};

// BEGIN KIT-14 pure helpers
const REPORT_RULES = [
  ["private-key", "block", /-----BEGIN [A-Z ]*PRIVATE KEY-----/],
  ["aws-access-key", "block", /AKIA[0-9A-Z]{16}/],
  ["github-token", "block", /gh[pousr]_[A-Za-z0-9]{36,}/],
  ["github-pat", "block", /github_pat_[A-Za-z0-9_]{22,}/],
  ["openai-key", "block", /sk-[A-Za-z0-9_-]{20,}/],
  ["stripe-live", "block", /sk_live_[A-Za-z0-9]{16,}/],
  ["slack-token", "block", /xox[baprs]-[A-Za-z0-9-]{10,}/],
  ["google-api-key", "block", /AIza[0-9A-Za-z_-]{30,}/],
  ["jwt", "block", /eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/],
  ["url-credentials", "block", /:\/\/[^/\s:@]+:[^/\s:@]+@/],
  ["bb-id", "block", /(^|[^A-Za-z0-9_])(thr_|proj_)[a-z0-9]{10}([^A-Za-z0-9_]|$)/],
  ["bb-id", "block", /(^|[^A-Za-z0-9_])ses_[A-Za-z0-9]{24,}([^A-Za-z0-9_]|$)/],
  ["private-ip", "block", /(^|[^0-9.])((10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|(192\.168\.[0-9]{1,3}\.[0-9]{1,3})|(172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}))([^0-9]|$)/],
  ["tailscale-host", "block", /[A-Za-z0-9-]+\.ts\.net/],
  ["home-dir", "block", /\/Users\/[A-Za-z0-9._-]+(\/|[^A-Za-z0-9._-]|$)/],
  ["email", "block", /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/],
  ["home-dir", "block", /\/home\/[A-Za-z0-9._-]+(\/|[^A-Za-z0-9._-]|$)/],
];

function scanReport(text, hostname = "") {
  const findings = [];
  const host = String(hostname || "");
  const escapedHost = host.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const hostPattern = host.length >= 4 && host !== "localhost"
    ? new RegExp(`(^|[^A-Za-z0-9_])${escapedHost}([^A-Za-z0-9_]|$)`, "i")
    : null;
  String(text).split("\n").forEach((line, index) => {
    for (const [rule, severity, pattern] of REPORT_RULES) {
      if (pattern.test(line)) findings.push({ rule, severity, line: index + 1 });
    }
    if (hostPattern?.test(line)) findings.push({ rule: "private-host", severity: "block", line: index + 1 });
  });
  return { blocked: findings.length > 0, findings };
}
// END KIT-14 pure helpers

const input = args && typeof args === "object" ? args : {};
const days = Number.isInteger(input.days) ? input.days : 7;
const post = input.post !== false;

const cellSchema = {
  type: "object", required: ["status", "evidence"], additionalProperties: false,
  properties: { status: { enum: ["PASS", "FAIL", "UNKNOWN"] }, evidence: { type: "string", minLength: 8 } },
};
const groupSchema = (stages) => ({
  type: "object", required: stages, additionalProperties: false,
  properties: Object.fromEntries(stages.map((stage) => [stage, cellSchema])),
});

phase("Find");
let runs = Array.isArray(input.runs) ? input.runs.map((thread) => ({ thread, folder: "" })) : null;
if (!runs) {
  const found = await agent(
    `Find every finished hivecall run: archived threads only, in all projects, archived in the last ${days} days. Active threads may still be working, so never include them.
1. List archived threads and keep only threads whose archivedAt is within the window.
2. For each, save its complete thread log to a temp file. Keep it only if it has a completed skill call named exactly hivecall and the log writes a run card (.hivecall/run.md).
3. Return each kept run with its thread id, archivedAt exactly as supplied by bb, and saved folder under ~/.hivecall/runs/*/ when present (otherwise an empty string).
4. Do not read run contents beyond this. If bb fails because BB_CLI is stale, run env -u BB_CLI bb ...`,
    { provider: "opencode", model: "openai/gpt-6-luna", reasoningLevel: "medium", label: "Find runs", phase: "Find",
      schema: { type: "object", required: ["runs"], additionalProperties: false, properties: { runs: { type: "array", items: {
        type: "object", required: ["thread", "folder", "archivedAt"], additionalProperties: false,
        properties: { thread: { type: "string" }, folder: { type: "string" }, archivedAt: { type: ["string", "number"] } },
      } } } } },
  );
  runs = found?.runs ?? [];
}
log(`${runs.length} run(s) to judge`);

if (runs.length === 0) {
  const report = `# Hivecall retro\n\nNo eligible archived runs were found in the last ${days} days.`;
  return { runs: 0, grids: [], report, taskKey: "", blocked: [] };
}

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
      if (!cell || !["PASS", "FAIL", "UNKNOWN"].includes(cell.status) || !cell.evidence)
        throw new Error(`Judge ${group} left stage ${stage} unanswered for ${run.thread}`);
      grid[stage] = cell;
    }
  });
  grids.push({ thread: run.thread, folder: run.folder, archivedAt: run.archivedAt, grid });
}

phase("Synthesize");
const synthesized = await agent(`Write a weekly hivecall retro from these fixed stage grids. Read ${PROFILE} ("Goal", "Privacy", and "Proposed fixes").

Run selection: judged every eligible run found in the last ${days} days. Total judged: ${grids.length}.
Grids:
${JSON.stringify(grids, null, 2)}

Past weeks: use only previous Hivecall retro task cards on the KIT board. Find them with bb tasks list --project KIT and read relevant cards with bb tasks show. Never search GitHub issues or post to GitHub.

Write a Markdown report with: (1) systemic wins and problems; (2) a table with one row per run and one column per stage; (3) one evidence line per FAIL, verified from the source record; (4) trends versus prior KIT retro cards; (5) up to three fixes from the profile. Include the total number of runs judged.

Privacy is mandatory: no secrets, tokens, personal names, emails, IPs, private or tailnet hosts, local paths, thread/project/session ids, or commit ids. Paraphrase owner messages and preserve only the behavior. Do not create, update or post any card, issue, or file. Run \`hostname -s\` and return its output verbatim in the required \`host\` field. Return the report as Markdown in \`markdown\`; do not include the host in the report.`,
  { provider: "opencode", model: "anthropic/claude-opus-5-5", reasoningLevel: "medium", label: "Synthesis", phase: "Synthesize",
    schema: { type: "object", required: ["markdown", "host"], additionalProperties: false, properties: { markdown: { type: "string" }, host: { type: "string" } } },
  },
);
if (typeof synthesized?.host !== "string" || synthesized.host.length === 0) {
  return { runs: grids.length, grids, report: "", taskKey: "", blocked: [{ rule: "private-host-unavailable", line: 0 }] };
}
const report = synthesized?.markdown ?? "";
const scan = scanReport(report, synthesized.host);
if (scan.blocked) {
  return { runs: grids.length, grids, report: "", taskKey: "", blocked: scan.findings.map(({ rule, line }) => ({ rule, line })) };
}
if (!post) return { runs: grids.length, grids, report, taskKey: "", blocked: [] };

phase("Post");
const posted = await agent(`Create exactly one new task card on the KIT board for this Hivecall retro report. Do not use GitHub or any public issue tracker. First write the exact Markdown below to a temporary UTF-8 file, then run: bb tasks create --project KIT --title "Hivecall retro — <today's local date>" --description-file <temp-file> --json. Return only the task key from the result. Do not change or omit report text.

Checked report:
${report}`,
  { provider: "opencode", model: "openai/gpt-6-luna", reasoningLevel: "medium", label: "Post KIT report", phase: "Post",
    schema: { type: "object", required: ["taskKey"], additionalProperties: false, properties: { taskKey: { type: "string" } } },
  },
);

return { runs: grids.length, grids, report, taskKey: posted?.taskKey ?? "", blocked: [] };
