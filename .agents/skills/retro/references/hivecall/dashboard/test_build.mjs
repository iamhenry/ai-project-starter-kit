import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { runInNewContext } from "node:vm";
import { spawnSync } from "node:child_process";

const directory = dirname(fileURLToPath(import.meta.url));
const temporary = mkdtempSync(join(tmpdir(), "hivecall-dashboard-"));
const build = join(temporary, "build.mjs");
const input = join(temporary, "results.jsonl");
const scores = value => Object.fromEntries(Array.from({ length: 7 }, (_, i) => [String(i + 1), i ? null : value]));
const trust = Object.fromEntries(Array.from({ length: 7 }, (_, i) => [String(i + 1), i ? "not-measured" : "ok"]));
const row = (date, tested, control_only, score) => ({
  date, week: "2026-W42", kind: "eval", tested, control_only, verdict: "rejected",
  targets: [1], scores: scores(score), trust: { ...trust }, deltas: { 1: 0 },
  report: ".agents/skills/retro/references/hivecall/dashboard/fixture/report.md",
  skill_commit: "fixture",
});

try {
  writeFileSync(build, readFileSync(join(directory, "build.mjs")));
  const notEvaluable = row("2026-10-14T12:00:00Z", "Filtered Pia evaluation", true, null);
  notEvaluable.trust["1"] = "not-evaluable";
  notEvaluable.deltas["1"] = null;
  writeFileSync(input, [
    row("2026-10-12T12:00:00Z", "Full evaluation", false, 75),
    row("2026-10-13T12:00:00Z", "Filtered B2 control", true, 5),
    notEvaluable,
  ].map(JSON.stringify).join("\n") + "\n");
  const result = spawnSync("node", [build, input], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);

  const html = readFileSync(join(temporary, "dashboard.html"), "utf8");
  const script = html.match(/<script>\n([\s\S]*?)\n<\/script>/)?.[1];
  assert.ok(script, "generated dashboard has its rendering script");
  const makeNode = tag => ({
    tag, attributes: {}, children: [], textContent: "",
    setAttribute(name, value) { this.attributes[name] = String(value); },
    append(...nodes) { this.children.push(...nodes); },
    replaceChildren(...nodes) { this.children = nodes; },
  });
  const elements = { chart: makeNode("svg"), history: makeNode("tbody") };
  runInNewContext(script, {
    document: {
      getElementById: id => elements[id],
      createElement: makeNode,
      createElementNS: (_namespace, tag) => makeNode(tag),
    },
    window: { addEventListener() {} },
  });

  const descendants = node => [node, ...node.children.flatMap(descendants)];
  const chartTitles = descendants(elements.chart).filter(node => node.tag === "title").map(node => node.textContent);
  assert.ok(chartTitles.some(title => title.includes("75/100")), "chart keeps the older full score");
  assert.ok(!chartTitles.some(title => /: 5\/100/.test(title)), "newer control score is excluded from trends");
  assert.equal(elements.history.children.length, 3, "full and filtered rows remain listed");
  assert.ok(elements.history.children.some(row =>
    /^PARTIAL \(filtered\) · Filtered B2 control$/.test(row.children[1].textContent)), "filtered control row stays labeled in the table");
  assert.ok(elements.history.children.some(row =>
    row.children[1].textContent === "PARTIAL (filtered) · Filtered Pia evaluation" && row.children[3].textContent === "#1 not evaluable"),
  "not-evaluable results render without a score gain");
} finally {
  rmSync(temporary, { recursive: true, force: true });
}

console.log("Dashboard filtered and not-evaluable result test passed.");
