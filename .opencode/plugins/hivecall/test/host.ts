import { mock } from "bun:test"
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { resolve } from "node:path"

// Drive the real plugin hooks with a fake OpenCode host; only the plugin wrapper is stubbed.
mock.module("@opencode/plugin", () => ({ Plugin: { define: (plugin: unknown) => plugin } }))
// Closed runs are archived under HIVECALL_HOME; keep tests out of the real home folder.
export const archiveHome = mkdtempSync(resolve(tmpdir(), "hive-home-"))
process.env.HIVECALL_HOME = archiveHome
const plugin = (await import("../index")).default as unknown as { setup(ctx: unknown): Promise<() => void> }

/** Teardown for every host; the test file runs these after each test. */
export const cleanups: Array<() => void> = []

/** `store` is the plugin's private storage; pass the same map and `root` to restart the plugin on an existing run. */
/** `live` adds the session APIs that deliver at once (synthetic messages, instruction entries); they are recorded in `sent`. */
export async function host({ card = false, store = new Map<string, unknown>(), root = "", live = false } = {}) {
  const restart = Boolean(root)
  root ||= mkdtempSync(resolve(tmpdir(), "hive-plugin-"))
  if (!restart) {
    mkdirSync(resolve(root, ".hivecall"))
    if (card) writeFileSync(resolve(root, ".hivecall/run.md"), "status: running\ngoal: g\nledger: .hivecall/checklist.html\n")
    writeFileSync(resolve(root, ".hivecall/checklist.html"), '<li id="ISC-001"><input type="checkbox"> a</li>')
    writeFileSync(resolve(root, ".hivecall/proof.txt"), "proof")
  }
  const hooks: Record<string, (event: Record<string, unknown>) => unknown> = {}
  const tools: Record<string, { execute(input: unknown, context: { sessionID: string }): Promise<{ content: string }> }> = {}
  const queue: Array<{ type: string; data: Record<string, unknown> }> = []
  const sent: Array<Record<string, unknown>> = []
  let wake: (() => void) | undefined
  const ctx = {
    location: { directory: root },
    event: { subscribe: ({ signal }: { signal: AbortSignal }) => (async function* () {
      signal.addEventListener("abort", () => wake?.())
      while (!signal.aborted) {
        if (queue.length) yield queue.shift()!
        else await new Promise<void>((done) => { wake = done })
      }
    })() },
    skill: { transform: async (edit: (editor: unknown) => void) => edit({ remove() {}, add() {} }) },
    command: { transform: async (edit: (editor: unknown) => void) => edit({ add() {} }) },
    session: { hook: async (name: string, fn: never) => { hooks[`session.${name}`] = fn }, prompt: async () => {},
      ...(live ? { synthetic: async (input: unknown) => { sent.push({ kind: "synthetic", ...(input as object) }) },
        instructions: { entry: { put: async (input: unknown) => { sent.push({ kind: "instruction", ...(input as object) }) } } } } : {}) },
    tool: { hook: async (name: string, fn: never) => { hooks[`tool.${name}`] = fn },
      transform: async (edit: (editor: unknown) => void) => edit({ add: (t: { name: string }) => { tools[t.name] = t as never } }) },
    storage: { get: async (k: string) => structuredClone(store.get(k)), set: async (k: string, v: unknown) => { store.set(k, structuredClone(v)) } },
  }
  const stop = await plugin.setup(ctx)
  cleanups.push(() => { stop(); rmSync(root, { recursive: true, force: true }) })
  let n = 0
  const session = { id: "ses-root" }
  const send = async (type: string, data: Record<string, unknown>) => {
    queue.push({ type, data }); wake?.()
    for (let i = 0; i < 5; i++) await Promise.resolve()
  }
  /**
   * Runs a tool call through the real hooks: `execute.before`, the tool's effect (a `write` writes its file; `exec` runs
   * anything else), then `execute.after`. Returns the block message the model would see, or null, and feeds the output back.
   */
  const call = async (tool: string, input: Record<string, unknown>, output = "", exec?: () => void) => {
    const id = `call_${++n}`
    try { hooks["tool.execute.before"]({ sessionID: session.id, id, tool, input }) } catch (error) { return (error as Error).message }
    if (tool === "write") writeFileSync(resolve(root, String(input.path)), String(input.content))
    exec?.()
    const after = { sessionID: session.id, id, tool, input, status: "completed", result: { content: [{ type: "text", text: output }] } }
    hooks["tool.execute.after"]?.(after)
    await send("session.tool.success", { sessionID: session.id, id, content: after.result.content })
    const seen = after.result.content.map((part) => part.text).join("\n")
    return seen === output ? null : seen
  }
  /** Runs one of the plugin's own tools between the real hooks; returns its output or the error the model would see. */
  const tool = async (name: string, input: Record<string, unknown>, sessionID = session.id) => {
    const id = `call_${++n}`
    try { hooks["tool.execute.before"]({ sessionID, id, tool: name, input }) } catch (error) { return (error as Error).message }
    let text = "", status = "completed"
    try { text = (await tools[name].execute(input, { sessionID })).content } catch (error) { text = (error as Error).message; status = "error" }
    const after = { sessionID, id, tool: name, input, status, result: { content: [{ type: "text", text }] } }
    hooks["tool.execute.after"]?.(after)
    return after.result.content.map((part) => part.text).join("\n")
  }
  /** A helper session records verdicts with hivecall_verdict: `"ISC-001 APPROVE_CODE, ISC-002 REVISE_CODE"`. */
  const verdict = (sessionID: string, spec: string) => tool("hivecall_verdict",
    { verdicts: spec.split(",").map((part) => part.trim().split(/\s+/)).map(([id, verdict]) => ({ id, verdict })) }, sessionID)
  /**
   * A native helper spawned by `parent`: linked at session.created, records each verdict spec (if any) with the tool,
   * then its spawn call returns. Returns the tool's last answer.
   */
  const helper = async ({ id, agent, prompt, child = `ses_${id}`, verdicts = [] as string | string[], background = false, parent = "ses-root" }:
    { id: string; agent: string; prompt: string; child?: string; verdicts?: string | string[]; background?: boolean; parent?: string }) => {
    hooks["tool.execute.before"]({ sessionID: parent, id, tool: "subagent", input: { agent, description: id, prompt, ...(background ? { background: true } : {}) } })
    await send("session.created", { sessionID: child, parentID: parent, agent })
    let answer = ""
    for (const spec of [verdicts].flat()) answer = await verdict(child, spec)
    await send("session.tool.success", { sessionID: parent, id, metadata: { sessionID: child, status: background ? "running" : "completed" }, content: [{ type: "text", text: "done" }] })
    return answer
  }
  const events = () => existsSync(resolve(root, ".hivecall/events.jsonl"))
    ? readFileSync(resolve(root, ".hivecall/events.jsonl"), "utf8").trim().split("\n").map((line) => JSON.parse(line)) : []
  return { root, store, stop, session, call, send, events, hooks, tool, tools, sent, verdict, helper, before: (event: Record<string, unknown>) => hooks["tool.execute.before"](event),
    after: (event: Record<string, unknown>) => hooks["tool.execute.after"](event),
    prompt: (text: string) => hooks["session.prompt"]({ sessionID: "ses-root", prompt: { text } }) }
}
