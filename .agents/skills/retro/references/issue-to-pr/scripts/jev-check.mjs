#!/usr/bin/env node
// Jev pre-check for the issue-to-PR retro. No dependencies (Node 22+).
//   node jev-check.mjs <thread_id>          preview: writes evals/last-request.json, sends nothing
//   node jev-check.mjs <thread_id> --send   asks Jev, prints findings, appends evals/results.jsonl
// Code counts facts; Jev answers narrow yes/no checks; the LLM judge decides. Findings are hints.
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { renderDashboard } from "./dashboard.mjs";

const SKILL = join(import.meta.dirname, "..");
const read = (p) => readFileSync(join(SKILL, p), "utf8");
const cfg = JSON.parse(read("jev-questions.json"));
const cases = JSON.parse(read("evals/cases.json"));
const [id, flag] = process.argv.slice(2);
if (id === "--dashboard") { renderDashboard(); process.exit(0); }
if (!/^thr_[a-z0-9]+$/.test(id ?? "")) throw new Error("usage: node jev-check.mjs <thread_id> [--send]");
if (flag && flag !== "--send") throw new Error("Unknown flag; use --send only after reviewing the preview.");
const hash = (value) => createHash("sha256").update(value).digest("hex");
const definitionHash = hash(["../../SKILL.md", "issue-to-pr.md", "jev-questions.json", "scripts/jev-check.mjs"].map(read).join("\n"));
const caseHash = hash(JSON.stringify(cases[id] ?? null));

// ---- drift guard: every question must still point at real rubric text ----
const sources = [cfg.routing._source, cfg.decision_question.source,
  ...Object.values(cfg.run_questions).map((q) => q.source), ...Object.values(cfg.helper_questions).map((q) => q.source)];
for (const s of sources) {
  const [file, text] = s.split(/:\s(.+)/);
  if (!read(file).replace(/\s+/g, " ").includes(text)) throw new Error(`Stale question: "${text}" no longer appears in ${file}. Update jev-questions.json.`);
}

// ---- 1. read the run (plain code) ----
const redact = (s) => s
  .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, "[email]")
  .replace(/\b(sk|pk|ghp|gho|ghs|github_pat|xox[bp])[-_][\w-]{10,}/g, "[secret]")
  .replace(/Bearer\s+\S+/gi, "Bearer [secret]")
  .replace(/\b[A-Za-z0-9+_-]{40,}\b/g, "[long-token]")
  .replace(/\/Users\/[^/\s]+/g, "/Users/[user]");
const bb = (...a) => execFileSync("bb", a, { encoding: "utf8", maxBuffer: 1e8 });
const secs = (d = "") => [...d.matchAll(/(\d+)([hms])/g)].reduce((t, [, v, u]) => t + v * { h: 3600, m: 60, s: 1 }[u], 0);
const clip = (s, n) => (s.length > n ? s.slice(0, n) + " …[trimmed]" : s);
function parse(log) {
  const turns = [], worked = [], events = [];
  for (const block of log.split(/^── /m).filter(Boolean)) {
    const [head, ...rest] = block.split("\n");
    const body = rest.join("\n").replace(/```[\s\S]*?```/g, "[code omitted]").trim();
    if (head.startsWith("Worked for")) worked.push(secs(head.match(/\((.+?)\)/)?.[1]));
    else if (/^(User|Assistant)/.test(head)) turns.push({ role: head.startsWith("User") ? "user" : "assistant", text: redact(body) });
    else if (/^(Stopped manually|Subagent finished)/.test(head)) events.push(redact(head.replace(/\s─+$/, "")));
  }
  return { turns, worked, events };
}
function collect() {
const run = parse(bb("thread", "log", id, "--all"));
const list = JSON.parse(bb("thread", "list", "--json"));
const helpers = (list.threads ?? list).filter((t) => t.parentThreadId === id).map((t) => {
  const p = parse(bb("thread", "log", t.id, "--all"));
  return {
    id: t.id,
    title: t.title,
    agent: t.title.match(/@([\w-]+) subagent/)?.[1] ?? "unknown",
    ended_on: p.turns.at(-1)?.role ?? "nothing",
    assignment: clip(p.turns.find((x) => x.role === "user")?.text ?? "", 700),
    final_message: p.turns.filter((x) => x.role === "assistant").at(-1)?.text ?? "",
  };
});

// ---- 2. build the two Jev requests ----
const decisions = read("issue-to-pr.md").split("\n").filter((l) => /^\| (Confirmed|Observed)/.test(l))
  .map((l) => l.split("|").map((c) => c.trim()).filter(Boolean));
const strip = ({ source, ...q }) => q;
const runQ = Object.fromEntries(Object.entries(cfg.run_questions).map(([k, q]) => [k, strip(q)]));
decisions.forEach(([status, decision, scope], i) => {
  runQ[`decision_${i + 1}_violated`] = { ...strip(cfg.decision_question),
    instructions: { decision: { status, decision, scope }, question: cfg.decision_question.instructions } };
});
const helperQ = {};
helpers.forEach((_, i) => {
  for (const [k, q] of Object.entries(cfg.helper_questions))
    helperQ[`helper_${i + 1}_${k}`] = { ...strip(q), instructions: q.instructions.replaceAll("{i}", i) };
});
const requests = {
  run: { model: cfg.model, state: { turns: run.turns.map((t) => ({ ...t, text: clip(t.text, 2500) })) }, questions: runQ },
  helpers: { model: cfg.model, state: { helpers: helpers.map(({ ended_on, ...h }) => h) }, questions: helperQ },
};
return { thread: id, definitionHash, caseHash, run, helpers, requests };
}
const previewPath = join(SKILL, "evals/last-request.json");
const packet = flag === "--send" ? JSON.parse(readFileSync(previewPath, "utf8")) : collect();
if (packet.thread !== id || packet.definitionHash !== definitionHash || packet.caseHash !== caseHash) throw new Error("Preview is stale or for another thread. Generate and review a new preview first.");
const { run, helpers, requests } = packet;
if (!flag) writeFileSync(previewPath, JSON.stringify(packet, null, 2));
const tok = (o) => Math.round(JSON.stringify(o.state).length / 4);
console.log(`preview: ${previewPath} · run state ~${tok(requests.run)} tok · helper state ~${tok(requests.helpers)} tok · ${Object.keys(requests.run.questions).length + Object.keys(requests.helpers.questions).length} questions`);
if (flag !== "--send") process.exit(0);

// ---- 3. ask Jev (two calls in parallel) ----
if (!process.env.OPENROUTER_API_KEY && existsSync(join(SKILL, ".env"))) process.loadEnvFile(join(SKILL, ".env"));
if (!process.env.OPENROUTER_API_KEY) throw new Error("OPENROUTER_API_KEY not set (env or .env in the skill folder)");
const ask = async (body) => {
  const res = await fetch("https://openrouter.ai/api/v1/systemone", {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(60000),
  });
  const j = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Jev ${res.status}: ${JSON.stringify(j)}`);
  for (const [key, question] of Object.entries(body.questions)) {
    const a = j.answers?.[key];
    if (a?.type !== question.type) throw new Error(`Missing or invalid answer: ${key}`);
    if (a.type === "noul" && !(Number.isFinite(a.noul) && a.noul >= 0 && a.noul <= 1)) throw new Error(`Invalid probability: ${key}`);
    if (a.type === "choice" && (!(a.choice in question.criteria) || !Number.isFinite(a.confidence) || a.confidence < 0 || a.confidence > 1)) throw new Error(`Invalid choice: ${key}`);
  }
  return j;
};
const [ra, ha] = await Promise.all([ask(requests.run), ask(requests.helpers)]);
const answers = { ...ra.answers, ...ha.answers };

// ---- 4. findings for the judge ----
const yn = (p) => (p >= cfg.yes_above ? "yes" : p <= cfg.no_below ? "no" : "unsure");
const findings = {};
const add = (k, value, by, detail) => (findings[k] = { value, by, detail });

const kinds = helpers.map((h, i) => {
  const a = answers[`helper_${i + 1}_job_kind`];
  const allowed = cfg.routing[a.choice];
  return { n: i + 1, agent: h.agent, kind: a.choice, sure: a.confidence >= 0.5, ok: allowed.includes(h.agent), allowed };
});
const bad = kinds.filter((k) => !k.ok);
add("helpers_misrouted", bad.some((k) => k.sure) ? "yes" : bad.length ? "unsure" : "no", "code+jev",
  bad.map((k) => `#${k.n} ${k.kind} ran on ${k.agent}, expected ${k.allowed.join("/")}${k.sure ? "" : " (unsure kind)"}`).join("; "));
const agents = new Set(helpers.map((h) => h.agent));
add("review_or_qa_missing", agents.has("reviewer") && agents.has("qa") ? "no" : "yes", "code", `helper agents: ${[...agents].join(", ")}`);
const errs = run.events.filter((e) => /error\)/.test(e));
const open = helpers.filter((h) => h.ended_on !== "assistant").length;
add("unfinished_helpers", errs.length + open ? "yes" : "no", "code", [...errs, open ? `${open} helper threads end without a reply` : ""].filter(Boolean).join("; "));
add("manual_stops", run.events.filter((e) => e.startsWith("Stopped")).length, "code", "");
add("longest_stretch_minutes", Math.round(Math.max(0, ...run.worked) / 60), "code", "");
const users = run.turns.filter((t) => t.role === "user").map((t) => t.text);
add("repeated_user_messages", users.length - new Set(users).size, "code", "");
for (const [k, a] of Object.entries(ra.answers)) add(k, yn(a.noul), "jev", a.noul.toFixed(2));
kinds.forEach((k) => add(`helper_${k.n}_clean_handoff`, yn(answers[`helper_${k.n}_clean_handoff`].noul), "jev",
  answers[`helper_${k.n}_clean_handoff`].noul.toFixed(2)));

for (const [k, f] of Object.entries(findings)) console.log(`${k.padEnd(30)} ${String(f.value).padEnd(7)} ${f.by.padEnd(9)} ${f.detail}`);

// ---- 5. score against the saved case, append one line ----
const exp = cases[id]?.expected;
const hits = exp ? Object.entries(exp).filter(([k, v]) => findings[k]?.value === v) : [];
const misses = exp ? Object.keys(exp).filter((k) => findings[k]?.value !== exp[k]) : [];
const git = (...a) => { try { return execFileSync("git", ["-C", SKILL, ...a], { encoding: "utf8" }).trim(); } catch { return ""; } };
const line = {
  date: new Date().toISOString(),
  thread: id,
  skill_version: read("../../SKILL.md").match(/version:\s*(\S+)/)?.[1] ?? "none",
  skill_commit: (git("log", "-1", "--format=%h", "--", "../..") || git("rev-parse", "--short", "HEAD")) + (git("status", "--porcelain", "--", "../..") ? "+dirty" : ""),
  model: ra.model,
  helper_model: ha.model,
  definition_hash: definitionHash,
  case_hash: caseHash,
  input_hash: hash(JSON.stringify({ run: requests.run.state, helpers: requests.helpers.state })),
  request_hash: hash(JSON.stringify(requests)),
  matched: hits.length,
  total: exp ? Object.keys(exp).length : 0,
  score_kind: "agreement on one tuning case; not pipeline quality",
  score: exp ? +(hits.length / Object.keys(exp).length).toFixed(2) : null,
  misses,
  cost: +((ra.usage.cost ?? 0) + (ha.usage.cost ?? 0)).toFixed(6),
  findings: Object.fromEntries(Object.entries(findings).map(([k, f]) => [k, f.value])),
  details: findings,
  answers,
  limitations: ["Agent names inferred from titles, not runtime configuration.", "Missing listed agents do not prove skipped gates; this run was aborted.", "Helper errors are not proof of dangling live processes.", "Displayed work durations are not billing or active-compute measurements.", "Source anchors cannot detect semantic drift.", "Same-case tuning is not independent validation."],
};
mkdirSync(join(SKILL, "evals/receipts"), { recursive: true });
line.receipt = `evals/receipts/${line.date.replaceAll(":", "-")}.json`;
writeFileSync(join(SKILL, line.receipt), JSON.stringify({ requests, responses: { run: ra, helpers: ha } }, null, 2));
appendFileSync(join(SKILL, "evals/results.jsonl"), JSON.stringify(line) + "\n");
renderDashboard();
console.log(`\nscore ${line.score ?? "n/a (no saved case)"}${misses.length ? ` · missed: ${misses.join(", ")}` : ""} · cost $${line.cost} · skill ${line.skill_version} (${line.skill_commit})`);
