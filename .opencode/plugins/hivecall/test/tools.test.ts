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
    h.before({ sessionID: "ses-root", id: "rev", tool: "subagent", input: { agent: "reviewer", description: "review ISC-1",
      prompt: "PROMISE: kind=helper rows=ISC-1 result=- lane=-\nTALK-BACK: report BUG only." } })
    await h.send("session.tool.success", { sessionID: "ses-root", id: "rev", metadata: { sessionID: "ses_rev", status: "completed" },
      content: [{ type: "text", text: "Decision: APPROVE_CODE" }] })
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
    h.before({ sessionID: "ses-root", id: "rev", tool: "subagent", input: { agent: "reviewer", description: "review ISC-1",
      prompt: "PROMISE: kind=helper rows=ISC-1 result=- lane=-\nTALK-BACK: report BUG only." } })
    await h.send("session.tool.success", { sessionID: "ses-root", id: "rev", metadata: { sessionID: "ses_rev", status: "completed" },
      content: [{ type: "text", text: "Decision: APPROVE_CODE" }] })
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
