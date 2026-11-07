import { afterEach, describe, expect, test } from "bun:test"
import { writeFileSync } from "node:fs"
import { resolve } from "node:path"
import { cleanups, host } from "./host"

// Run-card model policy, usage-limit failover, judge-model warning, immediate notices and rules after compaction.
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

const card = "status: running\ngoal: g\nledger: .hivecall/checklist.html\nmodels: build -> acme/fast#high, qa/reviewer -> acme/slow\nbackup models: qa -> acme/fast, build -> acme/spare\n"
const brief = (rows: string) => `PROMISE: kind=helper rows=${rows} result=- lane=-\nTALK-BACK: report BUG only.`
async function run(live = false) {
  const h = await host({ card: true, live })
  writeFileSync(resolve(h.root, ".hivecall/run.md"), card)
  await h.call("skill", { id: "hivecall" })
  await h.call("skill", { id: "subagent-delegation" })
  return h
}

describe("model policy", () => {
  test("fills the agent's run-card model, pauses once on an off-list model, then lets it through", async () => {
    const h = await run()
    const build = { agent: "build", description: "fix", prompt: brief("ISC-1") }
    expect(await h.call("subagent", build)).toBeNull()
    expect(build).toMatchObject({ model: "acme/fast#high" })
    const offList = { agent: "qa", description: "verify", prompt: brief("ISC-2"), model: "other/model" }
    expect(await h.call("subagent", offList)).toContain("qa may run on acme/slow or acme/fast")
    expect(await h.call("subagent", offList)).toBeNull()
  })

  test("warns when qa runs on the model that built its item", async () => {
    const h = await run()
    await h.call("subagent", { agent: "build", description: "fix", prompt: brief("ISC-1"), model: "acme/fast" })
    expect(await h.call("subagent", { agent: "qa", description: "verify", prompt: brief("ISC-1"), model: "acme/fast" }))
      .toContain("qa for ISC-001 runs on acme/fast, the model that built it")
  })
})

describe("immediate delivery", () => {
  test("a helper stopped by a usage limit is reported at once with the next allowed model", async () => {
    const h = await run(true)
    h.before({ sessionID: "ses-root", id: "spawn", tool: "subagent", input: { agent: "build", description: "fix", prompt: brief("ISC-1"), background: true } })
    await h.send("session.tool.success", { sessionID: "ses-root", id: "spawn", metadata: { sessionID: "ses_build", status: "running" }, content: [] })
    await h.send("session.execution.failed", { sessionID: "ses_build", error: { message: "You have hit your usage limit for this model." } })
    expect(h.sent.filter((row) => row.kind === "synthetic").map((row) => row.text).join("\n"))
      .toContain("stopped on a usage limit on acme/fast#high. Start a fresh helper with a Delta on the run card's next model for build: acme/spare.")
  })

  test("a foreground helper that hits its usage limit before its spawn returns still gets the next model", async () => {
    const h = await run(true)
    h.before({ sessionID: "ses-root", id: "spawn", tool: "subagent", input: { agent: "build", description: "fix", prompt: brief("ISC-1") } })
    await h.send("session.created", { sessionID: "ses_build", parentID: "ses-root", agent: "build" })
    await h.send("session.execution.failed", { sessionID: "ses_build", error: { message: "You have hit your usage limit for this model." } })
    expect(h.sent.filter((row) => row.kind === "synthetic").map((row) => row.text).join("\n"))
      .toContain("stopped on a usage limit on acme/fast#high. Start a fresh helper with a Delta on the run card's next model for build: acme/spare.")
  })

  test("a helper's unearned tick reaches the orchestrator at once, and the working rules are kept as an instruction entry", async () => {
    const h = await run(true)
    expect(h.sent.find((row) => row.kind === "instruction")).toMatchObject({ sessionID: "ses-root", key: "hivecall-rules" })
    h.session.id = "ses-helper"
    await h.call("write", { path: ".hivecall/checklist.html", content: '<li id="ISC-001"><input type="checkbox" checked> a</li>' })
    expect(h.sent.find((row) => row.kind === "synthetic")).toMatchObject({ sessionID: "ses-root" })
    expect(String(h.sent.find((row) => row.kind === "synthetic")?.text)).toContain("ISC-001 is ticked without")
    const before = h.sent.length
    await h.send("session.compaction.ended", { sessionID: "ses-root" })
    expect(h.sent.slice(before).map((row) => row.key)).toEqual(["hivecall-rules"])
  })
})
