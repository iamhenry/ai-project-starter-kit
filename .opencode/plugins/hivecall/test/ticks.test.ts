import { afterEach, describe, expect, test } from "bun:test"
import { appendFileSync, readFileSync, writeFileSync } from "node:fs"
import { basename, resolve } from "node:path"
import { archiveHome, cleanups, host } from "./host"

// Count only earned ticks, block the close: the ledger is judged as it stands after every call and never changed.
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

const ticked = '<li id="ISC-001"><input type="checkbox" checked> a</li>\n| ISC-001 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |'
const tick = { path: ".hivecall/checklist.html", content: ticked }
const close = { path: ".hivecall/run.md", content: "status: closed\ngoal: g\nledger: .hivecall/checklist.html\n## Final report\nDone" }
const brief = (rows: string) => `PROMISE: kind=helper rows=${rows} result=- lane=-\nTALK-BACK: report BUG only.`

/** A verified native reviewer approves ISC-001 with the verdict tool. */
async function approve(h: Awaited<ReturnType<typeof host>>) {
  await h.call("skill", { id: "subagent-delegation" })
  await h.helper({ id: "rev", agent: "reviewer", prompt: `slice=ISC-001\n${brief("ISC-001")}`, verdicts: "ISC-001 APPROVE_CODE" })
}
const tickRows = (h: Awaited<ReturnType<typeof host>>) => h.events()
  .filter((row) => row.type === "tick-unearned" || row.action === "tick" || row.type === "close-unearned").map((row) => `${row.type} ${row.id ?? row.ids}`)

describe("earned ticks", () => {
  test("discovery requires explicit promise rows and earns every promised item", async () => {
    for (const [rows, count] of [["-", 1], ["ISC-001,ISC-002", 2]] as const) {
      const h = await host({ card: true })
      await h.call("skill", { id: "subagent-delegation" })
      const answer = await h.helper({ id: "qa", agent: "qa", prompt: brief(rows), verdicts: count === 1 ? "ISC-001 REPRODUCED" : "ISC-001 REPRODUCED, ISC-002 REPRODUCED" })
      const ledger = "<h3>Discovery</h3>\n" + Array.from({ length: count }, (_, i) => `<li id="ISC-00${i + 1}"><input type="checkbox" checked> discovery</li>\n| ISC-00${i + 1} | PASS | commit abcdef1 | evidence .hivecall/proof.txt |`).join("\n")
      const result = await h.call("write", { path: ".hivecall/checklist.html", content: ledger })
      if (rows === "-") { expect(answer).toContain("ISC-001 is not one of the items your brief assigned"); expect(result).toContain("ISC-001 is ticked without") }
      else expect(result).toBeNull()
    }
  })
  test("discovery verdicts earn scoped ticks and allow close", async () => {
    const h = await host({ card: true })
    await h.call("skill", { id: "subagent-delegation" })
    await h.helper({ id: "qa", agent: "qa", prompt: brief("ISC-001"), verdicts: "ISC-001 REPRODUCED" })
    await h.helper({ id: "rev", agent: "reviewer", prompt: brief("ISC-002,ISC-003"), verdicts: "ISC-002 APPROVE_PLAN, ISC-003 SELECTED" })
    const ledger = "<h3>Discovery</h3>\n" + [1, 2, 3].map((n) => `<li id="ISC-00${n}"><input type="checkbox" checked> discovery</li>\n| ISC-00${n} | PASS | commit abcdef1 | evidence .hivecall/proof.txt |`).join("\n")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: ledger })).toBeNull()
    expect(await h.call("write", close)).toBeNull()
    // The closed run's record survives the worktree: events, run card and ledger are copied to the home folder.
    const archived = resolve(archiveHome, ".hivecall/runs", basename(h.root), "undated-run")
    expect(readFileSync(resolve(archived, "run.md"), "utf8")).toContain("status: closed")
    expect(readFileSync(resolve(archived, "checklist.html"), "utf8")).toContain("ISC-003")
    expect(readFileSync(resolve(archived, "events.jsonl"), "utf8")).toContain('"action":"tick"')
  })

  // Each case: the verdicts a helper records, in order (a later call corrects an earlier one), and whether the tick counts.
  for (const [agent, verdicts, heading, earned] of [
    ["qa", ["ISC-001 PASS"], "Discovery", true], ["qa", ["ISC-001 PASS"], "Build", false], ["qa", ["ISC-001 FAIL"], "Discovery", false],
    ["qa", ["ISC-001 NOT_REPRODUCED"], "Discovery", false], ["qa", ["ISC-001 PASS", "ISC-001 BLOCKED"], "Discovery", false],
    ["reviewer", ["ISC-001 APPROVE_PLAN"], "Build", false], ["reviewer", ["ISC-001 APPROVE_PLAN", "ISC-001 REVISE_PLAN"], "Discovery", false],
    ["reviewer", ["ISC-001 ASK_USER"], "Discovery", false], ["reviewer", ["ISC-001 REPRODUCED"], "Discovery", false],
    ["reviewer", ["ISC-001 REVISE_CODE", "ISC-001 APPROVE_CODE"], "Build", true], ["reviewer", ["ISC-001 APPROVE_CODE", "ISC-001 REVISE_CODE"], "Build", false],
    ["reviewer", [], "Build", false]] as const) {
    test(`${agent} ${JSON.stringify(verdicts)} on a ${heading} item ${earned ? "earns" : "does not earn"} a tick`, async () => {
      const h = await host({ card: true })
      await h.call("skill", { id: "subagent-delegation" })
      await h.helper({ id: "helper", agent, prompt: brief("ISC-001"), verdicts: [...verdicts] })
      const written = await h.call("write", { ...tick, content: `<h3>${heading}</h3>\n${ticked}` })
      if (earned) expect(written).toBeNull()
      else expect(written).toContain("ISC-001 is ticked without")
    })
  }
  test("an unearned tick blocks the close three times, then until the card says Not counted, then goes through with one warning", async () => {
    const h = await host({ card: true })
    expect(await h.call("write", tick)).toContain("ISC-001 is ticked without")
    for (let i = 0; i < 4; i++) expect(await h.call("write", close)).toContain("ticked without approval and receipt: ISC-001")
    expect(await h.call("write", close)).toContain("the run card must say `Not counted: ISC-001`")
    // Let through once the card names it, the close is still logged and told: it does not count the unearned tick.
    const listed = { ...close, content: `${close.content}\nNot counted: ISC-001 (never reviewed)` }
    expect(await h.call("write", listed)).toContain("The run card was closed while ISC-001")
    expect(h.events().filter((row) => row.rule === "no-early-done").map((row) => [row.type, row.count])).toEqual([
      ["blocked", 1], ["blocked", 2], ["blocked", 3], ["blocked", 4], ["blocked", 4], ["warning", undefined], ["close-unearned", undefined]])
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

  // Nov 1, 17:36Z: the orchestrator's tick was blamed on a reviewer whose `git diff` finished next.
  test("a ledger change is blamed on the one session with calls in flight, else unknown", async () => {
    const h = await host({ card: true })
    await h.call("shell", { command: "ls" })
    await h.call("shell", { command: "python3 tick.py" }, "", () => writeFileSync(resolve(h.root, ".hivecall/checklist.html"), ticked))
    h.before({ sessionID: "ses-rev", id: "diff", tool: "shell", input: { command: "git diff" } })
    h.after({ sessionID: "ses-rev", id: "diff", tool: "shell", input: {}, status: "completed", result: { content: [] } })
    const unearned = h.events().filter((row) => row.type === "tick-unearned" || row.type === "ledger-changed")
    expect(unearned.map((row) => [row.type, row.sessionID])).toEqual([["ledger-changed", "ses-root"], ["tick-unearned", "ses-root"]])

    const o = await host({ card: true })
    await o.call("shell", { command: "ls" })
    o.before({ sessionID: "ses-root", id: "a", tool: "shell", input: { command: "python3 tick.py" } })
    o.before({ sessionID: "ses-rev", id: "b", tool: "shell", input: { command: "git diff" } })
    writeFileSync(resolve(o.root, ".hivecall/checklist.html"), ticked)
    o.after({ sessionID: "ses-rev", id: "b", tool: "shell", input: {}, status: "completed", result: { content: [] } })
    o.after({ sessionID: "ses-root", id: "a", tool: "shell", input: {}, status: "completed", result: { content: [] } })
    expect(o.events().filter((row) => row.type === "tick-unearned").map((row) => row.sessionID)).toEqual(["unknown"])
  })

  test("a later qa FAIL un-counts a reviewer-approved tick", async () => {
    const h = await host({ card: true })
    await approve(h)
    expect(await h.call("write", tick)).toBeNull()
    await h.helper({ id: "qa", agent: "qa", prompt: brief("ISC-001"), verdicts: "ISC-001 FAIL" })
    expect(await h.call("shell", { command: "ls" })).toContain("ISC-001 is ticked without")
    expect(await h.call("write", close)).toContain("ticked without approval and receipt: ISC-001")
  })
})
