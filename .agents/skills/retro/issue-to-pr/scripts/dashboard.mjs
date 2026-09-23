import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const root = join(import.meta.dirname, "..");
export function renderDashboard() {
  const file = join(root, "evals/results.jsonl");
  const rows = existsSync(file) ? readFileSync(file, "utf8").split("\n").filter(Boolean).map(JSON.parse) : [];
  // Only dashboard fields go into the offline page, never raw transcript receipts.
  const data = rows.map(({ date, thread, skill_version, skill_commit, definition_hash, input_hash, case_hash, model, helper_model, score, misses, cost }) =>
    ({ date, thread, skill_version, skill_commit, definition_hash, input_hash, case_hash, model, helper_model, score, misses, cost }));
  const json = JSON.stringify(data).replaceAll("<", "\\u003c");
  const html = readFileSync(join(root, "dashboard.template.html"), "utf8").replace("/* RESULTS_JSON */[]", json);
  writeFileSync(join(root, "dashboard.html"), html);
  console.log(`Dashboard: ${join(root, "dashboard.html")}`);
}
