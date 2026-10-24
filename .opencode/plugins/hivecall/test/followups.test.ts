import { afterEach, describe, expect, test } from "bun:test"
import { Database } from "bun:sqlite"
import { readFileSync, writeFileSync } from "node:fs"
import { resolve } from "node:path"
import { cleanups, host } from "./host"
import { bbHelperSession, shellDelegation } from "../watchdog/adapters"
import { apply, memory, ruleFor } from "../watchdog/policy"

const brief = (agent = "qa") => `agent: ${agent}\nTALK-BACK: report BUG only.\nPROMISE: kind=helper rows=ISC-001 result=- lane=-\nslice=ISC-001`
const correction = "ISC-16 scope clarification: notes autosave is a separate undo action."
const close = { path: ".hivecall/run.md", content: "status: closed\ngoal: g\nledger: .hivecall/checklist.html\n## Final report\nParked with unlock." }
const kickoff = readFileSync(resolve(import.meta.dir, "../references/kickoff.md"), "utf8")
const parked = kickoff.match(/```html\n([\s\S]*?)```/)![1]
afterEach(() => { for (const cleanup of cleanups.splice(0)) cleanup() })

describe("active-helper follow-ups", () => {
  const spawn = async (h: Awaited<ReturnType<typeof host>>, thread: string, agent = "qa") => {
    await h.call("skill", { id: "subagent-delegation" })
    expect(await h.call("shell", { command: `bb thread spawn --prompt '${brief(agent)}'` }, `Thread spawned: ${thread}\n`)).toBeNull()
  }

  test("queued and steering corrections to an own unfinished BB helper need no repeated brief", async () => {
    const h = await host({ card: true })
    await spawn(h, "thr_active")
    expect(await h.call("shell", { command: `bb thread tell thr_active --mode queue '${correction}'` })).toBeNull()
    expect(await h.call("shell", { command: `bb thread tell thr_active --message-file - <<'EOF'\n${correction}\nEOF` })).toBeNull()
    expect(h.events().filter((e) => e.action === "tell").map((e) => e.type)).toEqual(["allowed", "allowed"])
  })

  test("finished targets are refused with or without a repeated brief", async () => {
    const h = await host({ card: true })
    await spawn(h, "thr_done")
    h.prompt("[bb system]\n\n@thread:thr_done completed:\n\nPASS: finished")
    for (const message of [correction, brief()])
      expect(await h.call("shell", { command: `bb thread tell thr_done --mode queue '${message}'` })).toContain("finished helper cannot be resumed")
  })

  test("unknown tells and fresh spawns still need the delegation skill and a full brief", async () => {
    for (const command of [`bb thread tell thr_unknown '${correction}'`, `bb thread spawn --prompt '${correction}'`]) {
      const h = await host({ card: true })
      expect(await h.call("shell", { command })).toContain("subagent-delegation")
      await h.call("skill", { id: "subagent-delegation" })
      expect(await h.call("shell", { command })).toContain("TALK-BACK")
    }
    const h = await host({ card: true })
    await h.call("skill", { id: "subagent-delegation" })
    expect(await h.call("shell", { command: `bb thread tell thr_unknown '${brief()}'` })).toBeNull()
  })

  test("another parent's helper and native subagent calls get no tell exemption", async () => {
    const h = await host({ card: true })
    h.session.id = "ses-other"
    await spawn(h, "thr_foreign")
    h.session.id = "ses-root"
    await h.call("skill", { id: "subagent-delegation" })
    expect(await h.call("shell", { command: `bb thread tell thr_foreign '${correction}'` })).toContain("TALK-BACK")
    await spawn(h, "thr_own")
    // The adapter, not a caller-supplied input field, marks a tell.
    expect(await h.call("subagent", { agent: "qa", sessionID: "thr_own", action: "tell", prompt: correction })).toContain("TALK-BACK")
  })

  test("the own-helper exemption never skips the two-revision fix limit", async () => {
    const h = await host({ card: true })
    await spawn(h, "thr_builder", "build")
    for (const id of ["r1", "r2"]) {
      h.before({ sessionID: "ses-root", id, tool: "subagent", input: { agent: "reviewer", prompt: brief("reviewer") } })
      await h.send("session.tool.success", { sessionID: "ses-root", id, metadata: { sessionID: `ses_${id}`, status: "completed" },
        content: [{ type: "text", text: "Decision: REVISE_CODE" }] })
    }
    expect(await h.call("shell", { command: "bb thread tell thr_builder 'ISC-001 fix implementation again'" })).toContain("Two REVISE_CODE")
  })

  test("a native helper's BB mirror resolves read-only, with ownership and completion protections", async () => {
    const h = await host({ card: true })
    const path = resolve(h.root, "bb.db"), db = new Database(path)
    db.exec("CREATE TABLE threads (id TEXT, parent_thread_id TEXT, status TEXT); CREATE TABLE events (thread_id TEXT, provider_thread_id TEXT)")
    db.exec("INSERT INTO threads VALUES ('thr_native', 'thr_parent', 'active'); INSERT INTO events VALUES ('thr_parent', 'ses-root'), ('thr_native', 'ses_native'), ('thr_native', 'ses_native')")
    db.close()
    const state = memory()
    apply(state, { type: "helper-created", sessionID: "ses_native", parentSessionID: "ses-root", agent: "qa" })
    const before = readFileSync(path)
    const mapped = bbHelperSession(state, "ses-root", "thr_native", path)
    expect(mapped).toBe("ses_native")
    const call = shellDelegation(`bb thread tell thr_native --mode queue '${correction}'`).call!
    call.input.sessionID = mapped!
    expect(ruleFor({ ...call, sessionID: "ses-root" }, state, h.root)).toBeNull()
    expect(bbHelperSession(state, "ses-other", "thr_native", path)).toBeNull()
    expect(bbHelperSession(memory(), "ses-root", "thr_native", path)).toBeNull()
    expect(bbHelperSession(state, "ses-root", "thr_native", path + ".missing")).toBeNull()
    expect(readFileSync(path)).toEqual(before)
    apply(state, { type: "helper-finished", sessionID: "ses_native" })
    expect(ruleFor({ ...call, sessionID: "ses-root" }, state, h.root)?.id).toBe("no-resume")
  })

  test("idle or ambiguous native mirror bindings get no unfinished-helper exemption", async () => {
    const h = await host({ card: true })
    const path = resolve(h.root, "bb.db"), db = new Database(path)
    db.exec("CREATE TABLE threads (id TEXT, parent_thread_id TEXT, status TEXT); CREATE TABLE events (thread_id TEXT, provider_thread_id TEXT)")
    db.exec("INSERT INTO threads VALUES ('thr_native', 'thr_parent', 'idle'); INSERT INTO events VALUES ('thr_parent', 'ses-root'), ('thr_native', 'ses_native')")
    const state = memory()
    apply(state, { type: "helper-created", sessionID: "ses_native", parentSessionID: "ses-root", agent: "qa" })
    expect(bbHelperSession(state, "ses-root", "thr_native", path)).toBeNull()
    // Completed native ids still resolve so no-resume wins even when BB is idle.
    apply(state, { type: "helper-finished", sessionID: "ses_native" })
    expect(bbHelperSession(state, "ses-root", "thr_native", path)).toBe("ses_native")
    db.exec("UPDATE threads SET status = 'active'; INSERT INTO events VALUES ('thr_native', 'ses_another')")
    apply(state, { type: "helper-created", sessionID: "ses_another", parentSessionID: "ses-root", agent: "qa" })
    expect(bbHelperSession(state, "ses-root", "thr_native", path)).toBeNull()
    db.close()
  })
})

describe("parking from kickoff instructions", () => {
  test("the documented unchecked marker saved first permits a later close, not a combined script", async () => {
    const h = await host({ card: true })
    const initial = parked.replace(' data-status="parked"', "")
    await h.call("write", { path: ".hivecall/checklist.html", content: initial })
    const command = `python3 - <<'PY'\nfrom pathlib import Path\nPath('.hivecall/checklist.html').write_text(${JSON.stringify(parked)})\nPath('.hivecall/run.md').write_text(${JSON.stringify(close.content)})\nPY`
    const blocked = await h.call("shell", { command }, "", () => {
      writeFileSync(resolve(h.root, ".hivecall/checklist.html"), parked)
      writeFileSync(resolve(h.root, ".hivecall/run.md"), close.content)
    })
    expect(blocked).toContain('data-status="parked"')
    expect(blocked).toContain("separate completed tool call")
    expect(blocked).toContain("open: ISC-23")
    expect(readFileSync(resolve(h.root, ".hivecall/checklist.html"), "utf8")).toBe(initial)
    expect(readFileSync(resolve(h.root, ".hivecall/run.md"), "utf8")).toContain("status: running")
    expect(await h.call("write", { path: ".hivecall/checklist.html", content: parked })).toBeNull()
    expect(await h.call("write", close)).toBeNull()
    expect(readFileSync(resolve(h.root, ".hivecall/run.md"), "utf8")).toBe(close.content)
    expect(h.events().some((e) => e.action === "tick")).toBe(false)
  })

  test("parking one criterion cannot hide another open or unearned criterion", async () => {
    const h = await host({ card: true })
    await h.call("write", { path: ".hivecall/checklist.html", content: parked + '\n<li id="ISC-2"><input type="checkbox"> ISC-2: open</li>' })
    expect(await h.call("write", close)).toContain("open: ISC-2")
    await h.call("write", { path: ".hivecall/checklist.html", content: parked + '\n<li id="ISC-2"><input type="checkbox" checked> ISC-2: unearned</li>\n| ISC-2 | PASS | commit abcdef1 | evidence .hivecall/proof.txt |' })
    expect(await h.call("write", close)).toContain("ticked without approval and receipt: ISC-002")
  })
})
