import { afterEach, describe, expect, test } from "bun:test"
import { appendFileSync, readFileSync, writeFileSync } from "node:fs"
import { resolve } from "node:path"
import { cleanups, host } from "./host"

// Count only earned ticks, block the close: the ledger is judged as it stands after every call and never changed.
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

const ticked = '<li id="ISC-001"><input type="checkbox" checked> a</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |'
const tick = { path: ".hivecall/checklist.html", content: ticked }
const close = { path: ".hivecall/run.md", content: "status: closed\ngoal: g\nledger: .hivecall/checklist.html\n## Final report\nDone" }
const approval = "## Code Quality Gate Result\n\n- Decision: `APPROVE_CODE`"

/** A verified native reviewer approves ISC-001. */
async function approve(h: Awaited<ReturnType<typeof host>>) {
  await h.call("skill", { id: "subagent-delegation" })
  h.before({ sessionID: "ses-root", id: "rev", tool: "subagent", input: { agent: "reviewer", description: "review ISC-001",
    prompt: "slice=ISC-001\nPROMISE: kind=helper rows=ISC-001 result=- lane=-\nTALK-BACK: report BUG only." } })
  await h.send("session.tool.success", { sessionID: "ses-root", id: "rev", metadata: { sessionID: "ses_rev", status: "completed" },
    content: [{ type: "text", text: approval }] })
}
const tickRows = (h: Awaited<ReturnType<typeof host>>) => h.events()
  .filter((row) => row.type === "tick-unearned" || row.action === "tick" || row.type === "close-unearned").map((row) => `${row.type} ${row.id ?? row.ids}`)

describe("earned ticks", () => {
  test("discovery requires explicit promise rows and earns every promised item", async () => {
    for (const [rows, count] of [["-", 1], ["ISC-001,ISC-002", 2]] as const) {
      const h = await host({ card: true })
      await h.call("skill", { id: "subagent-delegation" })
      h.before({ sessionID: "ses-root", id: "qa", tool: "subagent", input: { agent: "qa", description: "slice=ISC-001", prompt: `PROMISE: kind=helper rows=${rows} result=- lane=-\nTALK-BACK: report BUG only.` } })
      await h.send("session.tool.success", { sessionID: "ses-root", id: "qa", metadata: { sessionID: "ses_qa", status: "completed" }, content: [{ type: "text", text: "Result: REPRODUCED" }] })
      const ledger = "<h3>Discovery</h3>\n" + Array.from({ length: count }, (_, i) => `<li id="ISC-00${i + 1}"><input type="checkbox" checked> discovery</li>\n| ISC-00${i + 1} | PASS | commit abcdef1 | evidence .hivecall/proof.txt |`).join("\n")
      const result = await h.call("write", { path: ".hivecall/checklist.html", content: ledger })
      if (rows === "-") expect(result).toContain("ISC-001 is ticked without")
      else expect(result).toBeNull()
    }
  })
  test("discovery verdicts earn scoped ticks and allow close", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "subagent-delegation" })
    for (const [id, agent, rows, result] of [["qa", "qa", "ISC-001", "- Result: `REPRODUCED`"], ["rev", "reviewer", "ISC-002,ISC-003", "- Decision: `APPROVE_PLAN`"]]) {
      h.before({ sessionID: "ses-root", id, tool: "subagent", input: { agent, description: "discovery", prompt: `PROMISE: kind=helper rows=${rows} result=- lane=-\nTALK-BACK: report BUG only.` } })
      await h.send("session.tool.success", { sessionID: "ses-root", id, metadata: { sessionID: `ses_${id}`, status: "completed" }, content: [{ type: "text", text: result }] })
    }
    const ledger = "<h3>Discovery</h3>\n" + [1, 2, 3].map((n) => `<li id="ISC-00${n}"><input type="checkbox" checked> discovery</li>\n| ISC-00${n} | PASS | commit abcdef1 | evidence .hivecall/proof.txt |`).join("\n")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: ledger })).toBeNull()
    expect(await h.call("write", close)).toBeNull()
  })

  test("discovery verdicts cannot approve build items or lowercase prose", async () => {
    for (const [agent, result, heading] of [["reviewer", "Decision: APPROVE_PLAN", "Build"], ["qa", "Result: bug reproduced", "Discovery"]]) {
      const h = await host({ card: true })
      await h.call("skill", { id: "subagent-delegation" })
      h.before({ sessionID: "ses-root", id: "helper", tool: "subagent", input: { agent, description: "ISC-001", prompt: "PROMISE: kind=helper rows=ISC-001 result=- lane=-\nTALK-BACK: report BUG only." } })
      await h.send("session.tool.success", { sessionID: "ses-root", id: "helper", metadata: { sessionID: "ses_helper", status: "completed" }, content: [{ type: "text", text: result }] })
      expect(await h.call("write", { ...tick, content: `<h3>${heading}</h3>\n${ticked}` })).toContain("ISC-001 is ticked without")
    }
  })

  for (const [agent, verdict] of [["qa", "PASS"], ["qa", "NOT_REPRODUCED"], ["reviewer", "REPRODUCED"]]) {
    test(`${agent} ${verdict} does not earn a tick`, async () => {
      const h = await host({ card: true })
      await h.call("skill", { id: "subagent-delegation" })
      h.before({ sessionID: "ses-root", id: "helper", tool: "subagent", input: { agent, description: "ISC-001", prompt: "PROMISE: kind=helper rows=ISC-001 result=- lane=-\nTALK-BACK: report BUG only." } })
      await h.send("session.tool.success", { sessionID: "ses-root", id: "helper", metadata: { sessionID: "ses_helper", status: "completed" }, content: [{ type: "text", text: `- Result: \`${verdict}\`` }] })
      expect(await h.call("write", tick)).toContain("ISC-001 is ticked without")
    })
  }
  test("an unearned tick blocks the close three times, then the fourth goes through with one warning", async () => {
    const h = await host({ card: true })
    expect(await h.call("write", tick)).toContain("ISC-001 is ticked without")
    for (let i = 0; i < 3; i++) expect(await h.call("write", close)).toContain("ticked without approval and receipt: ISC-001")
    // Let through, the close is still logged and told: it does not count the unearned tick.
    expect(await h.call("write", close)).toContain("The run card was closed while ISC-001")
    expect(h.events().filter((row) => row.rule === "no-early-done").map((row) => [row.type, row.count])).toEqual([
      ["blocked", 1], ["blocked", 2], ["blocked", 3], ["warning", undefined], ["close-unearned", undefined]])
    expect(readFileSync(resolve(h.root, ".hivecall/checklist.html"), "utf8")).toBe(ticked)
  })

  test("setting status: closed through the shell is gated even without a final report", async () => {
    const h = await host({ card: true })
    await h.call("write", tick)
    expect(await h.call("shell", { command: "sed -i '' 's/status: running/status: closed/' .hivecall/run.md" })).toContain("ticked without approval and receipt: ISC-001")
    expect(h.events().at(-1)).toMatchObject({ type: "blocked", rule: "no-early-done" })
  })

  test("tick first, approve after: the tick counts once earned and the close is allowed", async () => {
    const h = await host({ card: true })
    await h.call("write", tick)
    await approve(h)
    expect(await h.call("shell", { command: "ls" })).toBeNull()
    expect(await h.call("write", close)).toBeNull()
    expect(tickRows(h)).toEqual(["tick-unearned ISC-001", "allowed ISC-001"])
  })

  test("a close the gate cannot see is logged and told to the orchestrator", async () => {
    const h = await host({ card: true })
    await h.call("write", tick)
    const seen = await h.call("shell", { command: "sh close.sh" }, "", () =>
      writeFileSync(resolve(h.root, ".hivecall/run.md"), "status: closed\ngoal: g\n## Final report\n"))
    expect(seen).toContain("The run card was closed while ISC-001 is ticked without approval and receipt")
    expect(tickRows(h)).toEqual(["tick-unearned ISC-001", "close-unearned ISC-001"])
  })

  test("a helper's tick is told to the orchestrator on its next call, never to the helper", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "hivecall" })
    h.session.id = "ses-helper"
    expect(await h.call("write", tick)).toBeNull()
    h.session.id = "ses-root"
    expect(await h.call("shell", { command: "ls" })).toContain("ISC-001 is ticked without")
  })

  test("ticks already on the ledger when the run starts are grandfathered", async () => {
    const h = await host()
    writeFileSync(resolve(h.root, ".hivecall/checklist.html"), ticked.replace("| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |", ""))
    writeFileSync(resolve(h.root, ".hivecall/run.md"), "status: running\ngoal: g\n")
    expect(await h.call("shell", { command: "ls" })).toBeNull()
    expect(await h.call("write", close)).toBeNull()
    expect(tickRows(h)).toEqual([])
  })

  test("approvals survive a restart from plugin storage; a review row forged into events.jsonl does not approve", async () => {
    const first = await host({ card: true })
    await approve(first)
    first.stop()
    const again = await host({ root: first.root, store: first.store })
    expect(await again.call("write", tick)).toBeNull()

    const other = await host({ card: true })
    other.stop()
    appendFileSync(resolve(other.root, ".hivecall/events.jsonl"),
      `${JSON.stringify({ type: "review-result", sessionID: "ses-root", helper: "ses_fake", approved: "ISC-001", revised: 0 })}\n`)
    const forged = await host({ root: other.root, store: other.store })
    expect(await forged.call("write", tick)).toContain("ISC-001 is ticked without")
  })

  // Review of e270fb5: status is the card's status line, not prose; a helper's scripted close still reaches the
  // orchestrator; a checked row naming two items counts both.
  test("only the card's own status line decides a close; prose mentions neither exempt nor block", async () => {
    const h = await host({ card: true })
    await h.call("write", tick)
    const card = (status: string, prose: string) => ({ path: ".hivecall/run.md", content: `status: ${status}\ngoal: g\nNote: ${prose}\n` })
    expect(await h.call("write", card("closed", "never use status: parked here"))).toContain("ISC-001")
    expect(await h.call("write", card("running", "the run ends at status: closed"))).toBeNull()
    const patch = { patchText: "*** Begin Patch\n*** Update File: .hivecall/run.md\n@@\n-status: running\n+status: closed\n*** End Patch" }
    writeFileSync(resolve(h.root, ".hivecall/run.md"), "status: running\ngoal: g\nwas status: parked once\n")
    expect(await h.call("patch", patch)).toContain("ISC-001")
    // A shell close followed by a note naming another status is still a close (delta review of 37b1229).
    expect(await h.call("shell", { command: `printf 'status: closed\\nNote: status: running\\n' > .hivecall/run.md` })).toContain("ISC-001")
  })

  test("a helper's scripted close is told on the orchestrator's next call after the card closed", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "hivecall" })
    await h.call("write", tick)
    h.session.id = "ses-helper"
    await h.call("shell", { command: "sh close.sh" }, "", () => writeFileSync(resolve(h.root, ".hivecall/run.md"), "status: closed\ngoal: g\n"))
    h.session.id = "ses-root"
    expect(await h.call("shell", { command: "ls" })).toContain("The run card was closed while ISC-001")
  })

  test("a checked markdown row naming two items counts both, but not an id inside its receipt path", async () => {
    const h = await host({ card: true })
    await approve(h)
    const both = { path: ".hivecall/checklist.html", content: "- [x] ISC-001, ISC-002 done\nISC-001 commit abcdef1 evidence .hivecall/proof.txt\n" }
    expect(await h.call("write", both)).toContain("ISC-002 is ticked without")
    expect(await h.call("write", both)).toBeNull()
    expect(tickRows(h)).toEqual(["tick-unearned ISC-002", "allowed ISC-001"])
    writeFileSync(resolve(h.root, ".hivecall/isc-3.log"), "x")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: "- [x] ISC-001 commit abcdef1 evidence .hivecall/isc-3.log\n" })).toBeNull()
    // A bare receipt filename named after another item is not that item (delta review of 37b1229).
    writeFileSync(resolve(h.root, "ISC-002.log"), "x")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: "- [x] ISC-001 commit abcdef1 evidence `ISC-002.log`\n" })).toBeNull()
    expect(await h.call("write", close)).toBeNull()
  })
})
