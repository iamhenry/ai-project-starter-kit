import { afterEach, describe, expect, test } from "bun:test"
import { copyFileSync, readFileSync, writeFileSync } from "node:fs"
import { resolve } from "node:path"
import { cleanups, host } from "./host"

// The orchestrator's ledger and run-card tools: proof checked before writing, one fixed format, loud errors, exact caller.
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

const template = resolve(import.meta.dir, "../references/checklist-template.html")
async function run() {
  const h = await host({ card: true })
  copyFileSync(template, resolve(h.root, ".hivecall/checklist.html"))
  await h.call("skill", { id: "hivecall" })
  return h
}
const ledger = (h: Awaited<ReturnType<typeof host>>) => readFileSync(resolve(h.root, ".hivecall/checklist.html"), "utf8")
const tick = { action: "tick", id: "ISC-1", observed: "total shows 10.00", evidence: ".hivecall/proof.txt", commit: "abcdef1", verifier: "Noor (qa)" }

describe("hivecall_ledger", () => {
  test("refuses an unearned tick with the reason and writes nothing", async () => {
    const h = await run()
    const before = ledger(h)
    expect(await h.tool("hivecall_ledger", tick)).toContain("ISC-001 would not count, so it was not ticked: no verified approval")
    expect(ledger(h)).toBe(before)
    expect(await h.tool("hivecall_ledger", { ...tick, evidence: "missing.txt" })).toContain("no receipt")
  })

  test("ticks an approved item in the template format, keeps progress true, and blames the caller", async () => {
    const h = await run()
    await h.call("skill", { id: "subagent-delegation" })
    await h.helper({ id: "rev", agent: "reviewer", prompt: "PROMISE: kind=helper rows=ISC-1 result=- lane=-\nTALK-BACK: report BUG only.", verdicts: "ISC-1 APPROVE_CODE" })
    expect(await h.tool("hivecall_ledger", tick)).toBe("tick ISC-001 written to .hivecall/checklist.html.")
    const text = ledger(h)
    expect(text).toContain('<li id="ISC-1"><input type="checkbox" disabled checked>')
    expect(text).toContain("<li>ISC-1: PASS - total shows 10.00; evidence .hivecall/proof.txt; verifier Noor (qa); commit abcdef1</li>")
    expect(text).toContain("<tr><th>progress</th><td>1/1</td></tr>")
    expect(h.events().filter((row) => row.type === "tick-unearned")).toEqual([])
    expect(h.events().find((row) => row.action === "tick" && row.type === "allowed")).toMatchObject({ id: "ISC-001", sessionID: "ses-root" })
  })

  test("a literal \\n in observed text stays on the receipt line (live smoke 2026-11-07)", async () => {
    const h = await run()
    await h.call("skill", { id: "subagent-delegation" })
    await h.helper({ id: "rev", agent: "reviewer", prompt: "PROMISE: kind=helper rows=ISC-1 result=- lane=-\nTALK-BACK: report BUG only.", verdicts: "ISC-1 APPROVE_CODE" })
    expect(await h.tool("hivecall_ledger", { ...tick, observed: "od -c 'a l p h a \\n'" })).toBe("tick ISC-001 written to .hivecall/checklist.html.")
  })

  test("fail, park and add use the kickoff formats; misses are loud", async () => {
    const h = await run()
    expect(await h.tool("hivecall_ledger", { action: "add", id: "ISC-2", text: "second — check: npm test", feature: "Feature name" })).toContain("add ISC-002")
    expect(await h.tool("hivecall_ledger", { action: "park", id: "ISC-2", reason: "needs device", unlock: "owner tests on phone" })).toContain("park ISC-002")
    expect(await h.tool("hivecall_ledger", { action: "fail", id: "ISC-1", reason: "rounding still wrong" })).toContain("fail ISC-001")
    const text = ledger(h)
    expect(text).toContain('<li id="ISC-2"><input type="checkbox" disabled data-status="parked"> ISC-2: second — check: npm test</li>')
    expect(text).toContain("<li>ISC-2: BLOCKED - parked; reason: needs device; unlock: owner tests on phone</li>")
    expect(text).toContain("<li>ISC-1: FAIL - rounding still wrong</li>")
    expect(await h.tool("hivecall_ledger", { action: "fail", id: "ISC-9", reason: "x" })).toContain("ISC-009 is not on the ledger. Nothing was written.")
    expect(await h.tool("hivecall_ledger", { ...tick, observed: "same as ISC-2" })).toContain("free text names ISC-002")
  })

  test("only the orchestrator may use it", async () => {
    const h = await run()
    h.session.id = "ses-helper"
    expect(await h.tool("hivecall_ledger", { action: "fail", id: "ISC-1", reason: "x" })).toContain("Only the run's orchestrator")
  })
})

describe("hivecall_card", () => {
  test("appends notes and sets status; closing is gated like a run-card write", async () => {
    const h = await run()
    expect(await h.tool("hivecall_card", { action: "note", section: "Lessons", text: "- builds need a clean cache" })).toBe("Run card updated.")
    expect(readFileSync(resolve(h.root, ".hivecall/run.md"), "utf8")).toContain("## Lessons\n- builds need a clean cache")
    expect(await h.tool("hivecall_card", { action: "status", status: "closed" })).toContain("(open: ISC-1)")
    expect(await h.tool("hivecall_card", { action: "status", status: "done" })).toContain("status must be one of")
  })
})

describe("hivecall_verdict", () => {
  const brief = "PROMISE: kind=helper rows=ISC-1 result=- lane=-\nTALK-BACK: report BUG only."

  test("only a linked reviewer or qa helper records a verdict; its brief is told how", async () => {
    const h = await run()
    await h.call("skill", { id: "subagent-delegation" })
    // The orchestrator cannot approve its own work, and a reviewer running as another agent cannot either.
    expect(await h.verdict("ses-root", "ISC-1 APPROVE_CODE")).toContain("not a reviewer or qa helper linked")
    expect(await h.helper({ id: "rev", agent: "reviewer", prompt: brief, verdicts: "ISC-1 APPROVE_CODE" })).toBe("Recorded: ISC-001 APPROVE_CODE.")
    const input = { agent: "reviewer", description: "rev2", prompt: brief }
    h.before({ sessionID: "ses-root", id: "rev2", tool: "subagent", input })
    expect(input.prompt).toContain("VERDICT: record your verdict for each item in your PROMISE rows with the hivecall_verdict tool")
    await h.send("session.created", { sessionID: "ses_rev2", parentID: "ses-root", agent: "build" })
    expect(await h.verdict("ses_rev2", "ISC-1 APPROVE_CODE")).toContain("not a reviewer or qa helper linked")
  })

  test("a reviewer that finishes without a recorded verdict approves nothing and the orchestrator is told at once", async () => {
    const h = await host({ card: true, live: true })
    copyFileSync(template, resolve(h.root, ".hivecall/checklist.html"))
    await h.call("skill", { id: "hivecall" })
    await h.call("skill", { id: "subagent-delegation" })
    await h.helper({ id: "rev", agent: "reviewer", prompt: brief })
    const told = h.sent.filter((m) => m.kind === "synthetic").map((m) => String(m.text)).join("\n")
    expect(told).toContain("reviewer ses_rev finished without a recorded verdict, so it approved nothing")
    expect(h.events().some((row) => row.type === "verdict-missing" && row.helper === "ses_rev")).toBe(true)
    expect(await h.tool("hivecall_ledger", tick)).toContain("would not count")
  })

  // Review of bc3d004.
  test("a helper spawned by another session, or known only from the event log, cannot record", async () => {
    const h = await run()
    await h.call("skill", { id: "subagent-delegation" })
    h.session.id = "ses-other-parent"
    await h.call("skill", { id: "subagent-delegation" })
    h.session.id = "ses-root"
    await h.helper({ id: "x", agent: "reviewer", prompt: brief, parent: "ses-other-parent" })
    expect(await h.verdict("ses_x", "ISC-1 APPROVE_CODE")).toContain("not a reviewer or qa helper linked")
    // A helper the event log names, after a restart, was never linked by this process.
    await h.helper({ id: "r", agent: "reviewer", prompt: brief })
    h.stop()
    const restarted = await host({ root: h.root, store: h.store })
    expect(await restarted.verdict("ses_r", "ISC-1 APPROVE_CODE")).toContain("not a reviewer or qa helper linked")
  })

  test("a repeated verdict is one attempt; a changed one corrects the earlier one", async () => {
    const h = await run()
    await h.call("skill", { id: "subagent-delegation" })
    await h.helper({ id: "rev", agent: "reviewer", prompt: brief, verdicts: ["ISC-1 REVISE_CODE", "ISC-1 REVISE_CODE", "ISC-1 APPROVE_CODE"] })
    const rows = h.events().filter((row) => row.type === "review-result")
    expect(rows.map((row) => row.verdicts)).toEqual(["ISC-001=REVISE_CODE", "ISC-001=APPROVE_CODE"])
    expect(await h.tool("hivecall_ledger", tick)).toBe("tick ISC-001 written to .hivecall/checklist.html.")
  })

  test("two foreground reviewers of one parent are told apart by their session title", async () => {
    const h = await run()
    await h.call("skill", { id: "subagent-delegation" })
    for (const id of ["a", "b"]) h.before({ sessionID: "ses-root", id, tool: "subagent", input: { agent: "reviewer", description: `review ${id}`,
      prompt: `PROMISE: kind=helper rows=ISC-${id === "a" ? 1 : 2} result=- lane=-\nTALK-BACK: report BUG only.` } })
    for (const id of ["a", "b"]) await h.send("session.created", { sessionID: `ses_${id}`, parentID: "ses-root", agent: "reviewer", title: `review ${id}` })
    expect(await h.verdict("ses_a", "ISC-1 APPROVE_CODE")).toBe("Recorded: ISC-001 APPROVE_CODE.")
    expect(await h.verdict("ses_b", "ISC-1 APPROVE_CODE")).toContain("ISC-001 is not one of the items your brief assigned (ISC-002)")
  })

})
