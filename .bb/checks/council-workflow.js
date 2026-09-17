const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const workflowPath = path.join(__dirname, "../workflows/council.js");
const source = fs.readFileSync(workflowPath, "utf8");

assert(source.startsWith("export const meta ="), "meta must be the first workflow statement");
assert(source.includes("const openingResults = await parallel("), "openings must fan out in parallel");
assert(source.includes("const voteResults = await parallel("), "votes must fan out in parallel");
assert(source.includes("const responseResults = await parallel("), "revisions must fan out in parallel");
assert(source.includes("round <= maxRounds"), "configured maxRounds must control termination");
assert(!/\bMAX_ROUNDS\b/.test(source), "the workflow must not use a fixed MAX_ROUNDS constant");
assert(source.includes('const DEFAULT_CONSENSUS_MODE = "majority";'), "omitted consensus mode must default to majority");
assert(!/\bmodels\b/.test(source), "model selection must not be a workflow input");
const roleModels = {
  synthesizer: ["openai/gpt-6-astra", "low"],
  logician: ["ollama-cloud/kimi-k3", "high"],
  critic: ["openai/gpt-5.6-sol", "medium"],
  researcher: ["ollama-cloud/glm-5.3-flash", "high"],
  creative: ["ollama-cloud/glm-5.3", "high"],
};
for (const [role, [model, reasoningLevel]] of Object.entries(roleModels)) {
  const start = source.indexOf(`case "${role}":`);
  assert(start >= 0, `${role} must have a direct model selection`);
  const end = source.indexOf("\n      case ", start + 1);
  const selection = source.slice(start, end === -1 ? source.length : end);
  assert(selection.includes('provider: "opencode",'), `${role} provider must be a direct literal`);
  assert(selection.includes(`model: "${model}",`), `${role} model must be the requested direct literal`);
  assert(selection.includes(`reasoningLevel: "${reasoningLevel}",`), `${role} reasoning level must be the requested direct literal`);
}
assert.equal((source.match(/^\s*provider: "opencode",$/gm) || []).length, 5, "each role must select the provider with a direct literal");
assert.equal((source.match(/^\s*model: "[^"]+",$/gm) || []).length, 5, "each role must select a model with a direct literal");
assert.equal((source.match(/^\s*reasoningLevel: "(?:low|medium|high)",$/gm) || []).length, 5, "each role must select a reasoning level with a direct literal");
assert(source.includes("if (debug) {\n  result.transcript = transcript;\n}"), "transcript must be debug-only in the result");

const start = source.indexOf("// BEGIN deterministic protocol helpers");
const end = source.indexOf("// END deterministic protocol helpers");
assert(start >= 0 && end > start, "deterministic helper section must exist");

const context = {};
vm.runInNewContext(
  `${source.slice(start, end)}
globalThis.council = {
  proposerForRound,
  evaluateVotes,
  fallbackPosition,
  fallbackProposal,
  fallbackVote,
  fallbackSynthesis,
  transcriptEntry,
  summarizeVotes,
};`,
  context,
);

const council = context.council;
assert.deepEqual(
  [1, 2, 3, 4, 5].map(council.proposerForRound),
  ["researcher", "logician", "creative", "critic", "researcher"],
  "proposer rotation must follow the four-role order",
);

const accepts = (count) => Array.from({ length: 4 }, (_, index) => ({
  decision: index < count ? "accept" : "reject",
}));
assert.equal(council.evaluateVotes(accepts(4), 1, 5, "unanimous"), "consensus");
assert.equal(council.evaluateVotes(accepts(3), 1, 5, "unanimous"), "proposing");
assert.equal(council.evaluateVotes(accepts(3), 1, 5, "majority"), "consensus");
assert.equal(council.evaluateVotes(accepts(2), 1, 5, "majority"), "proposing");
assert.equal(council.evaluateVotes(accepts(2), 2, 2, "majority"), "dissent");
assert.equal(council.evaluateVotes(accepts(0), 1, 1, "unanimous"), "dissent");
assert.equal(council.evaluateVotes(accepts(0), 2, 5, "unanimous"), "proposing");

assert.equal(JSON.stringify(council.transcriptEntry("opening", "researcher", 0, "{}")), JSON.stringify({
  kind: "opening",
  role: "researcher",
  round: 0,
  content: "{}",
}));
assert.equal(council.fallbackPosition("critic").summary, "[no response]");
assert.equal(council.fallbackProposal("researcher", 1).resolution, "[no proposal]");
assert.equal(council.fallbackVote("logician").decision, "reject");
assert.equal(council.fallbackSynthesis(), "[synthesis unavailable]");
assert.equal(JSON.stringify(council.summarizeVotes(accepts(3), "majority")), JSON.stringify({
  mode: "majority",
  accepts: 3,
  rejects: 1,
  total: 4,
}));

console.log("council workflow deterministic checks passed");
