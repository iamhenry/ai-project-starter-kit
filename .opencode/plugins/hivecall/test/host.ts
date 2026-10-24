import { mock } from "bun:test"
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { resolve } from "node:path"

// Drive the real plugin hooks with a fake OpenCode host; only the plugin wrapper is stubbed.
mock.module("@opencode/plugin", () => ({ Plugin: { define: (plugin: unknown) => plugin } }))
const plugin = (await import("../index")).default as unknown as { setup(ctx: unknown): Promise<() => void> }

/** Teardown for every host; the test file runs these after each test. */
export const cleanups: Array<() => void> = []

/** `store` is the plugin's private storage; pass the same map and `root` to restart the plugin on an existing run. */
export async function host({ card = false, store = new Map<string, unknown>(), root = "" } = {}) {
  const restart = Boolean(root)
  root ||= mkdtempSync(resolve(tmpdir(), "hive-plugin-"))
  if (!restart) {
    mkdirSync(resolve(root, ".hivecall"))
    if (card) writeFileSync(resolve(root, ".hivecall/run.md"), "status: running\ngoal: g\nledger: .hivecall/checklist.html\n")
    writeFileSync(resolve(root, ".hivecall/checklist.html"), '<li id="ISC-001"><input type="checkbox"> a</li>')
    writeFileSync(resolve(root, ".hivecall/proof.txt"), "proof")
  }
  const hooks: Record<string, (event: Record<string, unknown>) => unknown> = {}
  const queue: Array<{ type: string; data: Record<string, unknown> }> = []
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
    session: { hook: async (name: string, fn: never) => { hooks[`session.${name}`] = fn }, prompt: async () => {} },
    tool: { hook: async (name: string, fn: never) => { hooks[`tool.${name}`] = fn } },
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
  const events = () => existsSync(resolve(root, ".hivecall/events.jsonl"))
    ? readFileSync(resolve(root, ".hivecall/events.jsonl"), "utf8").trim().split("\n").map((line) => JSON.parse(line)) : []
  return { root, store, stop, session, call, send, events, hooks, before: (event: Record<string, unknown>) => hooks["tool.execute.before"](event),
    after: (event: Record<string, unknown>) => hooks["tool.execute.after"](event),
    prompt: (text: string) => hooks["session.prompt"]({ sessionID: "ses-root", prompt: { text } }) }
}
