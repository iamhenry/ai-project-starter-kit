import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, copyFileSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

test("offline dashboard preserves history, handles no runs, and escapes embedded data", async () => {
  const root = mkdtempSync(join(tmpdir(), "retro-dashboard-"));
  try {
    mkdirSync(join(root, "scripts"));
    mkdirSync(join(root, "evals"));
    copyFileSync(join(import.meta.dirname, "dashboard.mjs"), join(root, "scripts/dashboard.mjs"));
    copyFileSync(join(import.meta.dirname, "../dashboard.template.html"), join(root, "dashboard.template.html"));
    const { renderDashboard } = await import(pathToFileURL(join(root, "scripts/dashboard.mjs")));
    renderDashboard();
    const extract = () => JSON.parse(readFileSync(join(root, "dashboard.html"), "utf8").match(/const rows = (.*);/)[1]);
    assert.deepEqual(extract(), []);
    const rows = [
      { date: "2026-09-23T00:00:00Z", thread: "fixture", score: .89, cost: .001 },
      { date: "2026-09-23T01:00:00Z", thread: "</script><script>unsafe()</script>", score: .5, cost: .002, requests: "private transcript" },
    ];
    const history = rows.map(JSON.stringify).join("\n") + "\n";
    writeFileSync(join(root, "evals/results.jsonl"), history);
    renderDashboard();
    assert.equal(extract().length, 2);
    assert.equal(extract()[1].thread, rows[1].thread);
    assert.equal(extract()[1].score, .5);
    const html = readFileSync(join(root, "dashboard.html"), "utf8");
    assert.ok(!html.includes("</script><script>unsafe()"));
    assert.ok(!html.includes("private transcript"));
    assert.equal(readFileSync(join(root, "evals/results.jsonl"), "utf8"), history);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
