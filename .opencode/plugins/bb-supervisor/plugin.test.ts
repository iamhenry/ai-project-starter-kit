import { expect, mock, test } from "bun:test"
import { Database } from "bun:sqlite"
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"

// Drive the real hooks with a fake host; only the plugin wrapper and the BB CLI are stubbed.
mock.module("@opencode/plugin", () => ({ Plugin: { define: (plugin: unknown) => plugin } }))
const mod = await import("./index")
const plugin = mod.default as unknown as { setup(ctx: unknown): Promise<() => void> }
const told: Array<{ thread: string; message: string }> = []
mod.bb.mission = () => ({ id: "thr_mission", parent: "thr_root" })
mod.bb.tell = (thread, message) => { told.push({ thread, message }); return true }

// Plugin storage that outlives one host, so a second host on the same store is a plugin reload.
const store = () => {
  const data = new Map<string, unknown>()
  return { data, set: async (key: string, value: unknown) => { data.set(key, structuredClone(value)) },
    scan: async ({ prefix }: { prefix: string }) => ({ entries: [...data].filter(([k]) => k.startsWith(prefix)).map(([key, value]) => ({ key, value: structuredClone(value) })) }) }
}

async function host(storage = store(), existing?: string) {
  const dir = existing ?? mkdtempSync(join(tmpdir(), "bbsup-test-"))
  if (!existing) {
    Bun.spawnSync(["git", "-C", dir, "init", "-q"])
    writeFileSync(join(dir, "scratch.txt"), "hello\n")
  }
  const hooks: Record<string, (event: Record<string, unknown>) => unknown> = {}
  const queue: unknown[] = [], sent: Array<{ sessionID: string; text: string }> = []
  let wake: (() => void) | undefined
  const stop = await plugin.setup({
    location: { directory: dir },
    storage,
    event: { subscribe: ({ signal }: { signal: AbortSignal }) => (async function* () {
      signal.addEventListener("abort", () => wake?.())
      while (!signal.aborted) if (queue.length) yield queue.shift(); else await new Promise<void>((r) => (wake = r))
    })() },
    session: { hook: async (name: string, fn: never) => { hooks[`session.${name}`] = fn }, prompt: async (p: never) => { sent.push(p) } },
    tool: { hook: async (name: string, fn: never) => { hooks[`tool.${name}`] = fn } },
  })
  const emit = async (type: string, data: Record<string, unknown>) => { queue.push({ type, data }); wake?.(); await Bun.sleep(20) }
  const prompt = (sessionID: string, text: string) => hooks["session.prompt"]({ sessionID, prompt: { text } })
  const gate = async (sessionID: string, id: string, agent: string, verdict: string, receipt?: string) => {
    hooks["tool.execute.before"]({ sessionID, id, tool: "subagent", input: { agent } })
    if (receipt) writeFileSync(receipt, "observed: scratch.txt reads hello\n") // the qa run writes its proof
    await emit("session.tool.success", { sessionID, id, content: [{ text: receipt ? `${verdict}\nReceipt: ${receipt}` : verdict }] })
  }
  const done = async (sessionID: string, text = "ENDING: DONE\nAdded the line.") => {
    await emit("session.text.ended", { sessionID, text })
    await emit("session.execution.succeeded", { sessionID })
  }
  return { dir, storage, sent, emit, prompt, gate, done, hooks, stop }
}

test("a Supervisor cannot launch a Mission without TALK-BACK; only presence is checked", async () => {
  const h = await host()
  try {
    const file = join(h.dir, "brief with spaces.md")
    const run = (command: string, agent = "bb-supervisor", tool = "shell") => () => h.hooks["tool.execute.before"]({
      sessionID: "root", id: "spawn", agent, tool, input: { command, workdir: h.dir },
    })
    for (const size of ["SMALL", "LARGE"]) {
      const brief = `MISSION: ${size}\nRole: Mission Lead\n`
      writeFileSync(file, brief)
      expect(run("bb thread spawn --prompt-file 'brief with spaces.md'")).toThrow("SKILL.md (Talk-back)")
      expect(run(`bb thread spawn --prompt '${brief}'`, "bb-supervisor", "bash")).toThrow("Mission launch refused")
      expect(run(`bb thread spawn --prompt '${brief}not TALK-BACK: inline mention'`)).toThrow("Mission launch refused")
      expect(run(`bb thread spawn --prompt-file '${file}'`, "build")).not.toThrow()
      writeFileSync(file, `${brief}TALK-BACK: any wording\n`)
      expect(run(`bb thread spawn --prompt-file='${file}'`)).not.toThrow()
      expect(run(`bb thread spawn --prompt '${brief}TALK-BACK:'`)).not.toThrow()
    }
    expect(run("bb thread spawn --prompt 'Ordinary task'")).not.toThrow()
    expect(run("bb thread tell thr_m --message-file 'brief with spaces.md'")).not.toThrow()
  } finally { h.stop() }
})

test("a small Mission that reports done without QA is sent back, naming the missing QA pass", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  await h.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("fresh qa PASS")
  expect(h.sent[0].text).not.toContain("reviewer APPROVE_CODE")

  // A fresh background qa PASS then lets the done report through; no send-back while it runs.
  h.hooks["tool.execute.before"]({ sessionID: "m", id: "q1", tool: "subagent", input: { agent: "qa", background: true } })
  await h.emit("session.tool.success", { sessionID: "m", id: "q1", metadata: { sessionID: "q", status: "running" }, content: [] })
  await h.emit("session.execution.succeeded", { sessionID: "m" })
  const proof = join(h.dir, "qa-result.md") // a receipt inside the worktree does not void the gates
  writeFileSync(proof, "observed: scratch.txt reads hello\n")
  await h.emit("session.inbox.enqueued", { sessionID: "m", item: { type: "synthetic", payload: { text: `Verdict: PASS\n[report](${proof})`, metadata: { source: "subagent", childID: "q", state: "completed" } } } })
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  h.stop()
})

test("a change made after approval and QA, by any route, voids both", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  await h.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  await h.gate("m", "q1", "qa", "Verdict: PASS", join(h.dir, "result.md"))
  writeFileSync(join(h.dir, "scratch.txt"), "hello\nsneaky\n") // e.g. a shell write after the gates
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("files changed after it")
  h.stop()
})

test("a source edit made while qa runs is not blessed by its PASS", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  await h.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  h.hooks["tool.execute.before"]({ sessionID: "m", id: "q1", tool: "subagent", input: { agent: "qa" } })
  writeFileSync(join(h.dir, "scratch.txt"), "hello\nfixed during qa\n")
  const proof = join(h.dir, "proof.md")
  writeFileSync(proof, "observed\n")
  await h.emit("session.tool.success", { sessionID: "m", id: "q1", content: [{ text: `Verdict: PASS\nReceipt: ${proof}` }] })
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("reviewer APPROVE_CODE of the current files (files changed after it)")
  h.stop()
})

test("deleting or changing the receipt after the PASS voids it", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  const proof = join(h.dir, "proof.md")
  await h.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  await h.gate("m", "q1", "qa", "Verdict: PASS", proof)
  writeFileSync(proof, "")
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("its receipt file was deleted or changed after the PASS")
  h.stop()
})

test("a qa PASS without a receipt written during its run does not count", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  const old = join(h.dir, "old-report.md")
  writeFileSync(old, "stale proof\n") // already there before the qa run
  await h.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  await h.gate("m", "q1", "qa", "Verdict: PASS (looked fine)")
  await h.done("m")
  await h.gate("m", "q2", "qa", `Verdict: PASS\nReceipt: ${old}`)
  await h.done("m")
  await h.gate("m", "q3", "qa", "Verdict: PASS", old) // rewriting an existing file during qa is not a receipt
  await h.done("m")
  expect(h.sent).toHaveLength(3)
  for (const s of h.sent) expect(s.text).toContain("named no receipt file written during its run")
  h.sent.length = 0
  await h.gate("m", "r2", "reviewer", "Decision: APPROVE_CODE") // q3 changed old-report.md, so approve again
  await h.gate("m", "q4", "qa", "Verdict: PASS", join(h.dir, "fresh.md"))
  await h.done("m")
  expect(h.sent).toHaveLength(0)
  h.stop()
})

test("after the last send-back the root is told to treat the Mission as BLOCKED", async () => {
  told.length = 0
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  for (let i = 0; i < 5; i++) await h.done("m")
  expect(h.sent).toHaveLength(3)
  expect(told).toHaveLength(1)
  expect(told[0].thread).toBe("thr_root")
  expect(told[0].message).toContain("Treat it as BLOCKED")
  h.stop()
})

test("an honest ending other than DONE is not sent back; a report with no ENDING line is", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\napply the style guide")
  await h.done("m", "ENDING: NEEDS DECISION\nThe style guide does not exist. Which file did you mean?")
  expect(h.sent).toHaveLength(0)
  await h.done("m", "All finished.")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("ENDING")
  h.stop()
})

test("a helper whose brief is qa work cannot run as build", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  const run = (agent: string) => () => h.hooks["tool.execute.before"]({ sessionID: "m", id: agent, tool: "subagent",
    input: { agent, description: "Verify the line", prompt: "Act as the verification-gate QA for this change." } })
  expect(run("build")).toThrow("would run as `build`. Run it as `qa` instead.")
  expect(run("qa")).not.toThrow()
  h.stop()
})

test("a QA pass from before a newer approval does not count", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  await h.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  await h.gate("m", "q1", "qa", "Verdict: PASS", join(h.dir, "result.md"))
  await h.gate("m", "r2", "reviewer", "Decision: APPROVE_CODE")
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("fresh qa PASS")
  h.stop()
})

test("after a plugin reload the Mission is still gated and keeps its send-back count", async () => {
  const a = await host()
  a.prompt("m", "MISSION: SMALL\nadd a line")
  await a.done("m")
  expect(a.sent).toHaveLength(1)
  a.stop()
  const b = await host(a.storage, a.dir) // reloaded plugin, same storage and checkout
  await b.done("m")
  expect(b.sent).toHaveLength(1)
  expect(b.sent[0].text).toContain("send-back 2/3")
  b.stop()
})

// A fake BB database with a root thread (ses_root) and one Mission (ses_m); returns its path.
function bbDb() {
  const home = mkdtempSync(join(tmpdir(), "bbsup-home-"))
  mkdirSync(join(home, ".bb"))
  const db = new Database(join(home, ".bb/bb.db"))
  db.run("CREATE TABLE threads (id TEXT, title TEXT, status TEXT, project_id TEXT, environment_id TEXT, parent_thread_id TEXT, archived_at TEXT, deleted_at TEXT, created_at TEXT)")
  db.run("CREATE TABLE events (thread_id TEXT, provider_thread_id TEXT)")
  db.run("INSERT INTO threads VALUES ('thr_root','root','idle','p','e',NULL,NULL,NULL,'1'), ('thr_m','🚀 add a line','idle','p','e','thr_root',NULL,NULL,'2')")
  db.run("INSERT INTO events VALUES ('thr_root','ses_root'), ('thr_m','ses_m')")
  db.close()
  return join(home, ".bb/bb.db")
}
const rootStatus = (h: Awaited<ReturnType<typeof host>>) => {
  const event = { agent: "bb-supervisor", sessionID: "ses_root", system: [] as Array<{ text: string }> }
  h.hooks["session.context"](event)
  return event.system.map((part) => part.text).join("\n")
}

test("the root's status rechecks an accepted Mission and stops calling it done when its receipt changes", async () => {
  const realDb = mod.bb.db
  mod.bb.db = bbDb()
  try {
    const h = await host()
    const status = () => rootStatus(h)
    const proof = join(h.dir, "result.md")
    h.prompt("ses_m", "MISSION: SMALL\nadd a line")
    await h.gate("ses_m", "r1", "reviewer", "Decision: APPROVE_CODE")
    await h.gate("ses_m", "q1", "qa", "Verdict: PASS", proof)
    await h.done("ses_m")
    expect(status()).toContain("gate: DONE accepted")
    rmSync(proof)
    expect(status()).toContain("gate: not done: files or the receipt changed after it was accepted")
    h.stop()
  } finally { mod.bb.db = realDb }
})

test("an accepted status with no gate record to recheck does not count", async () => {
  const realDb = mod.bb.db
  mod.bb.db = bbDb()
  try {
    const storage = store()
    await storage.set("gate/ses_m", "DONE accepted (fresh review, fresh QA, receipt intact)") // saved before gates were stored
    const h = await host(storage)
    expect(rootStatus(h)).toContain("gate: not done: its acceptance cannot be rechecked")
    h.stop()
  } finally { mod.bb.db = realDb }
})

test("a Mission caught running as the wrong agent stays caught after a reload", async () => {
  told.length = 0
  const a = await host()
  a.prompt("m", "MISSION: SMALL\nadd a line")
  await a.emit("session.created", { sessionID: "m", agent: "general" })
  expect(told).toHaveLength(1)
  a.stop()
  const b = await host(a.storage, a.dir)
  await b.emit("session.created", { sessionID: "m", agent: "general" })
  await b.gate("m", "r1", "reviewer", "Decision: APPROVE_CODE")
  await b.gate("m", "q1", "qa", "Verdict: PASS", join(b.dir, "result.md"))
  await b.done("m")
  expect(told).toHaveLength(1) // the root is not told twice
  expect(b.sent).toHaveLength(1)
  expect(b.sent[0].text).toContain("runs as general")
  b.stop()
})

test("only an overall APPROVE_CODE approves; ASK_USER with a per-item approval does not", async () => {
  const h = await host()
  h.prompt("m", "MISSION: SMALL\nadd a line")
  await h.gate("m", "r1", "reviewer", "Decision: ASK_USER\nISC-1: APPROVE_CODE")
  await h.done("m")
  expect(h.sent).toHaveLength(1)
  expect(h.sent[0].text).toContain("reviewer APPROVE_CODE")
  h.stop()
})

test("a subagent handed a copy of the brief is not gated", async () => {
  const h = await host()
  h.prompt("child", "You are a subagent.\n\nMISSION: SMALL\nreview this")
  await h.done("child")
  expect(h.sent).toHaveLength(0)
  h.stop()
})
