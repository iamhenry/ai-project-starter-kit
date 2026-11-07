import { createHash } from "node:crypto"
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"
import { dirname, relative, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"
import { allowedModels, modelPolicy, usageLimit } from "./watchdog/models"
import { editCard, editLedger, type CardEdit, type LedgerEdit } from "./watchdog/tools"
import { bbAgentStamp, bbHelperSession, bbNoticeEvents, bbOutputRead, bbPinEvent, bbReadEvent, bbSpawnEvent, shellDelegation, stampSucceeded, type BbStamp } from "./watchdog/adapters"
import { activeLedger, activeRun, agentMismatch, archiveRun, anchor, apply, blockDecision, briefRole, canaryMissing, dirtyFiles, fillBrief, helperIdentity, iscId, memory, replanEvents, reviewEvent, ruleFor, tickedItems, tickProblems, unearned, type HiveEvent, type Violation } from "./watchdog/policy"

const pluginDir = dirname(fileURLToPath(import.meta.url))
const skillPath = resolve(pluginDir, "SKILL.md")
const howToPath = resolve(pluginDir, "HOW-TO-WORK.md")
const rulePath = resolve(pluginDir, "rules.json")
const rules = JSON.parse(readFileSync(rulePath, "utf8")) as Array<{ id: string; message: string }>

function logFailure(operation: string, error: unknown) {
  try { console.error(`[hivecall] ${operation} failed (${error instanceof Error ? error.name : "unknown error"})`) } catch {}
}

/** The child's own result inside the exact `<subagent …>` envelope the host built; null if the text is not that envelope. */
function subagentBody(text: string, header: string): string | null {
  return text.startsWith(`${header}\n`) && text.endsWith("\n</subagent>") ? text.slice(header.length + 1, -"\n</subagent>".length) : null
}

export default Plugin.define({
  id: "hivecall",
  async setup(ctx) {
    const root = ctx.location.directory
    const runDir = resolve(root, ".hivecall")
    const eventsPath = resolve(runDir, "events.jsonl")
    const cardPath = resolve(runDir, "run.md")
    const state = memory()
    const warned = new Set<string>()
    const skillCalls = new Map<string, string>()
    const childParents = new Map<string, string>()
    // Pending tool calls whose success output feeds helper state: native reviewers, BB spawns and BB output reads.
    const toolCalls = new Map<string, { identity: ReturnType<typeof helperIdentity>; background: boolean }>()
    // Background native helpers (identity in `state.helpers`) still awaiting their result, which arrives later as a
    // synthetic message in the parent.
    const backgroundHelpers = new Set<string>()
    const bbSpawns = new Map<string, ReturnType<typeof helperIdentity>>()
    const bbReads = new Map<string, NonNullable<ReturnType<typeof bbOutputRead>>>()
    const bbStamps = new Map<string, BbStamp>()
    // A verified project pin arms the very next call in that session; if that call is a spawn into the same project
    // whose brief names the same role, the new thread counts as pinned (`spawnPins`, by call id).
    const projectPins = new Map<string, BbStamp>()
    const spawnPins = new Map<string, string>()
    // The agent each session runs as and the role its first brief names, to warn when they differ.
    const sessionAgents = new Map<string, string>()
    const sessionRoles = new Map<string, string>()
    const mismatched = new Set<string>()
    const pendingCalls: Array<Map<string, unknown>> = [skillCalls, toolCalls, bbSpawns, bbReads, bbStamps, spawnPins]
    const forget = (callID: string) => { for (const pending of pendingCalls) pending.delete(callID) }
    // Loading the hivecall skill arms the hooks before the run card exists; after that the card's status decides.
    let armed = false
    const live = () => activeRun(root) || (armed && !existsSync(resolve(runDir, "run.md")))

    const record = (entry: Record<string, string | number | undefined>) => {
      try {
        mkdirSync(runDir, { recursive: true })
        appendFileSync(eventsPath, `${JSON.stringify({ at: new Date().toISOString(), ...entry })}\n`)
      } catch (error) { logFailure("event recording", error) }
    }
    // State always follows what happened; the log is only written while a run is active.
    const emit = (event: HiveEvent | null) => {
      if (!event) return
      const approved = state.approvals.size
      apply(state, event)
      if (live()) record(event)
      if (state.approvals.size !== approved) save()
    }
    // Warn only: a helper whose real agent differs from the role its brief names.
    const mismatch = (sessionID: string, helper: string, role: string, agent: string) => {
      if (!agentMismatch(role, agent) || mismatched.has(helper)) return
      mismatched.add(helper)
      if (live()) record({ type: "agent-mismatch", sessionID, helper, brief: role, agent })
    }
    const key = (sessionID: string, rule: string) => `${sessionID}:${rule}`
    // One warning row per session and rule once the 3-block cap lets a violation through.
    const warnOnce = (sessionID: string, rule: string) => {
      if (warned.has(key(sessionID, rule))) return
      warned.add(key(sessionID, rule))
      record({ type: "warning", rule, sessionID })
    }
    // Tick state the event log must not forge (approvals, the ticks a run started with, the orchestrator's sessions) lives
    // in plugin storage; events.jsonl is writable by any shell in the run.
    const storeKey = `hivecall:${root}`
    const orchestrators = new Set<string>()
    let started = false // the grandfathered ticks were recorded for this run
    const save = () => {
      void Promise.resolve(ctx.storage?.set(storeKey, { approvals: [...state.approvals], grandfathered: [...state.grandfathered],
        started, orchestrators: [...orchestrators] })).catch((error) => logFailure("storage write", error))
    }
    // Who changed the ledger (invariant 3): the ledger is hashed before and after every call; a change is blamed on the
    // one session with calls in flight, else "unknown", never a guess. `tickedBy` keeps that blame per newly ticked id.
    const inFlight = new Map<string, string>() // callID -> sessionID
    const tickedBy = new Map<string, string>()
    let seen: { path: string; hash: string; ticked: Set<string> } | null = null
    const inFlightActor = () => {
      const sessions = new Set(inFlight.values())
      return sessions.size === 1 ? [...sessions][0] : "unknown"
    }
    const observeLedger = (actor = inFlightActor()) => {
      if (!live()) return
      const path = activeLedger(root)
      const text = existsSync(path) ? readFileSync(path, "utf8") : ""
      const hash = createHash("sha1").update(text).digest("hex")
      if (seen && seen.path === path && seen.hash === hash) return
      const ticked = new Set(tickedItems(text))
      if (seen) {
        for (const id of ticked) if (!seen.ticked.has(id)) tickedBy.set(id, actor)
        record({ type: "ledger-changed", sessionID: actor, calls: inFlight.size })
      }
      seen = { path, hash, ticked }
    }
    const flagged = new Set<string>(), earned = new Set<string>() // ids already logged as unearned / earned
    const notices: string[] = [] // waiting for the orchestrator's next completed call
    const warnings: string[] = [] // warn-only notices, delivered the same way
    let wasActive = activeRun(root)
    // The run's record is kept outside the worktree, which is deleted when it is archived: copied every 10 minutes
    // while the run is live (runs that never close still reach the retro) and once more on close.
    let archivedAt = 0
    const archive = () => {
      archivedAt = Date.now()
      try { archiveRun(root, process.env.HIVECALL_HOME || homedir()) } catch (error) { logFailure("run archive", error) }
    }
    // Ticks already on the ledger before the first call of an active run are grandfathered, judged before that call runs.
    const startRun = () => {
      if (started || !activeRun(root)) return
      const ledger = activeLedger(root)
      started = true
      for (const id of tickedItems(existsSync(ledger) ? readFileSync(ledger, "utf8") : "")) state.grandfathered.add(id)
      save()
    }
    // A helper's call never carries the notice; with no recorded orchestrator, any top-level session that is not a helper does.
    const isOrchestrator = (sessionID: string) => orchestrators.size ? orchestrators.has(sessionID)
      : !childParents.has(sessionID) && !state.helpers.has(sessionID)
    const arm = (sessionID: string) => {
      armed = true
      if (!activeRun(root) && (started || state.approvals.size || state.failures.size || state.sinceTick)) { // a fresh run: forget the last run's tick state
        state.approvals.clear(); state.grandfathered.clear(); state.failures.clear(); state.replans.clear(); state.sinceTick = 0; started = false; orchestrators.clear(); flagged.clear(); earned.clear()
      }
      if (sessionID && !orchestrators.has(sessionID)) orchestrators.add(sessionID)
      putRules(sessionID)
      save()
    }

    // Notices reach the orchestrator at once as a synthetic message (P9); when that is unavailable or fails they wait for
    // its next completed call, as before.
    const session = ctx.session as unknown as { synthetic?: (input: { sessionID: string; text: string }) => Promise<unknown>
      instructions?: { entry?: { put?: (input: { sessionID: string; key: string; value: string }) => Promise<void> } } }
    const orchestratorID = () => [...orchestrators].at(-1)
    const flush = (exceptSessionID = "") => {
      const target = orchestratorID()
      if (!(notices.length || warnings.length) || !session.synthetic || !target || target === exceptSessionID) return
      const text = outbox()
      void session.synthetic.call(ctx.session, { sessionID: target, text }).catch((error) => { logFailure("notice delivery", error); warnings.push(text) })
    }
    const outbox = () => {
      const rule = notices.length ? ` ${rules.find((r) => r.id === "tick-gate")?.message ?? ""}` : ""
      return [notices.length ? `[hivecall] ${notices.splice(0).join(" ")}${rule}` : "", ...warnings.splice(0).map((w) => w.startsWith("[hivecall]") ? w : `[hivecall] ${w}`)]
        .filter(Boolean).join("\n")
    }
    // The working rules survive compaction as a session instruction entry, not a re-read the model may skip (P8).
    const rulesText = () => {
      const text = readFileSync(howToPath, "utf8")
      const start = text.indexOf("## Invariants"), end = text.indexOf("## Defaults")
      return `Hivecall working rules (HOW-TO-WORK.md):\n${text.slice(start < 0 ? 0 : start, end < 0 ? undefined : end).trim()}`
    }
    const putRules = (sessionID: string) => {
      if (!sessionID || !session.instructions?.entry?.put) return
      try { void session.instructions.entry.put.call(ctx.session, { sessionID, key: "hivecall-rules", value: rulesText() }).catch((error) => logFailure("rules entry", error)) }
      catch (error) { logFailure("rules entry", error) }
    }
    // Model each native helper runs on, by call then by session, and models builders used per item (P5-P7).
    const spawnModels = new Map<string, { agent: string; model: string }>()
    const helperModels = new Map<string, { agent: string; model: string; parent: string }>()
    const builderModels = new Map<string, Set<string>>()

    try {
      if (existsSync(eventsPath)) {
        for (const line of readFileSync(eventsPath, "utf8").split(/\r?\n/)) {
          try {
            const event = JSON.parse(line)
            if (event.type === "warning" && event.sessionID && event.rule) warned.add(key(event.sessionID, event.rule))
            if (event.type === "tick-unearned" && event.id) flagged.add(String(event.id))
            if (event.type === "allowed" && event.action === "tick" && event.id) { earned.add(String(event.id)); flagged.delete(String(event.id)) }
            apply(state, event)
          } catch { /* Ignore a partial final JSONL row. */ }
        }
      }
    } catch (error) { logFailure("event restoration", error) }
    state.approvals.clear() // replayed review rows may be forged; approvals come from storage only
    try {
      const stored = await ctx.storage?.get(storeKey) as { approvals?: string[]; grandfathered?: string[]; started?: boolean; orchestrators?: string[] } | undefined
      for (const id of stored?.approvals ?? []) state.approvals.add(id)
      for (const id of stored?.grandfathered ?? []) state.grandfathered.add(id)
      for (const id of stored?.orchestrators ?? []) orchestrators.add(id)
      started = stored?.started === true
    } catch (error) { logFailure("storage read", error) }

    const controller = new AbortController()
    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        try {
          const data = (event as { data?: Record<string, unknown> }).data ?? {}
          if ((event.type === "session.created" || event.type === "session.agent.selected") && typeof data.sessionID === "string" && typeof data.agent === "string")
            sessionAgents.set(data.sessionID, data.agent)
          if (event.type === "session.skill.activated" && data.id === "hivecall") arm(typeof data.sessionID === "string" ? data.sessionID : "")
          if (event.type === "session.compaction.ended" && typeof data.sessionID === "string" && orchestrators.has(data.sessionID) && live()) putRules(data.sessionID)
          // A helper stopped by a usage limit: tell the orchestrator now, with the run card's next allowed model (P6).
          if (event.type === "session.execution.failed" && typeof data.sessionID === "string" && live()) {
            const helper = helperModels.get(data.sessionID)
            const parent = helper?.parent ?? childParents.get(data.sessionID) ?? state.helpers.get(data.sessionID)?.parentSessionID
            if (parent && usageLimit(JSON.stringify(data))) {
              const agent = helper?.agent || state.helpers.get(data.sessionID)?.agent || ""
              const next = allowedModels(modelPolicy(existsSync(cardPath) ? readFileSync(cardPath, "utf8") : ""), agent).filter((model) => model !== helper?.model)
              record({ type: "helper-usage-limit", sessionID: data.sessionID, parentSessionID: parent, agent, model: helper?.model ?? "" })
              warnings.push(`Helper ${data.sessionID}${agent ? ` (${agent})` : ""} stopped on a usage limit${helper?.model ? ` on ${helper.model}` : ""}. ` +
                (next.length ? `Start a fresh helper with a Delta on the run card's next model for ${agent}: ${next[0]}.` : `The run card lists no other model for ${agent || "this agent"}; add one under backup models: or set status: waiting-usage.`))
              flush()
            }
          }
          if (event.type === "session.created" && typeof data.sessionID === "string" && typeof data.parentID === "string") {
            childParents.set(data.sessionID, data.parentID)
            // A foreground helper can fail before its spawn call returns: bind its model now when exactly one open spawn
            // from this parent, for this agent, carries one (the spawn result binds it otherwise).
            const open = [...spawnModels].filter(([callID, spawned]) => callID.startsWith(`${data.parentID}:`) &&
              (typeof data.agent !== "string" || spawned.agent === data.agent))
            if (open.length === 1 && !helperModels.has(data.sessionID)) {
              helperModels.set(data.sessionID, { ...open[0][1], parent: data.parentID })
              spawnModels.delete(open[0][0])
            }
            // Skip when the spawn result already recorded this helper with its identity; a bare row would erase it on restore.
            if (live() && !state.helpers.has(data.sessionID)) record({ type: "helper-created", sessionID: data.sessionID, parentSessionID: data.parentID })
          }
          if (event.type === "session.execution.succeeded" && typeof data.sessionID === "string") {
            if (childParents.has(data.sessionID)) emit({ type: "helper-finished", sessionID: data.sessionID, parentSessionID: childParents.get(data.sessionID)! })
            // Native helpers are checked at spawn; this covers helpers started outside this session tree, such as BB threads.
            else mismatch(data.sessionID, data.sessionID, sessionRoles.get(data.sessionID) ?? "", sessionAgents.get(data.sessionID) ?? "")
          }
          // A background native helper's final result reaches its parent as a synthetic message; OpenCode 2.1.3 publishes
          // it as `session.inbox.enqueued` with a `synthetic` item (the `session.synthetic` shape is accepted too).
          const item = data.item && typeof data.item === "object" ? data.item as Record<string, unknown> : {}
          const synthetic = event.type === "session.inbox.enqueued" && item.type === "synthetic" && item.payload && typeof item.payload === "object"
            ? item.payload as Record<string, unknown> : event.type === "session.synthetic" ? data : null
          const metadata = synthetic?.metadata && typeof synthetic.metadata === "object" ? synthetic.metadata as Record<string, unknown> : {}
          const childID = typeof metadata.childID === "string" ? metadata.childID : ""
          const helper = backgroundHelpers.has(childID) ? state.helpers.get(childID) : undefined
          if (metadata.source === "subagent" && metadata.state !== "running" && helper?.parentSessionID === data.sessionID) {
            backgroundHelpers.delete(childID)
            // Only the child's own text is a verdict; the envelope also echoes the parent's `description`.
            const body = metadata.state === "completed" ? subagentBody(String(synthetic?.text ?? ""),
              `<subagent sessionID="${childID}" state="completed" description="${String(synthetic?.description ?? "")}">`) : null
            if (body !== null) emit(reviewEvent(helper.parentSessionID, childID, helper, body, root))
            else if (metadata.state === "completed") logFailure("background helper result envelope not recognised", new Error("unrecognised envelope"))
          }
          if (event.type === "session.tool.failed" && typeof data.sessionID === "string" && typeof data.id === "string") {
            forget(`${data.sessionID}:${data.id}`)
            inFlight.delete(`${data.sessionID}:${data.id}`)
            spawnModels.delete(`${data.sessionID}:${data.id}`)
          }
          // A session that stopped has no calls in flight, even if a hook never saw their end.
          if (/^session\.(?:execution\.(?:succeeded|failed)|deleted)$/.test(event.type) && typeof data.sessionID === "string")
            for (const [callID, owner] of inFlight) if (owner === data.sessionID) inFlight.delete(callID)
          if (event.type === "session.deleted" && typeof data.sessionID === "string") {
            const gone = data.sessionID
            for (const table of [childParents, sessionAgents, sessionRoles, projectPins]) table.delete(gone)
            for (const child of backgroundHelpers) if (child === gone || state.helpers.get(child)?.parentSessionID === gone) backgroundHelpers.delete(child)
            for (const table of pendingCalls) for (const callID of table.keys()) if (callID.startsWith(`${gone}:`)) table.delete(callID)
          }
          if (event.type === "session.tool.success" && typeof data.sessionID === "string" && typeof data.id === "string") {
            const callID = `${data.sessionID}:${data.id}`
            const result = Array.isArray(data.content) ? data.content.map((part) =>
              part && typeof part === "object" && "text" in part ? String(part.text) : "").join("\n") : ""
            if (skillCalls.get(callID) === "subagent-delegation") emit({ type: "skill-loaded", sessionID: data.sessionID, id: "subagent-delegation" })
            const native = toolCalls.get(callID), spawn = bbSpawns.get(callID), read = bbReads.get(callID)
            if (native) {
              // The spawn result names the helper's session (`metadata.sessionID`); tie the brief's identity to it.
              const metadata = data.metadata && typeof data.metadata === "object" ? data.metadata as Record<string, unknown> : {}
              const child = typeof metadata.sessionID === "string" ? metadata.sessionID : /\bsessionID:\s*(ses_\w+)/.exec(result)?.[1]
              // The host's status is authoritative; the launch notice text is a fallback for hosts that omit it.
              const background = typeof metadata.status === "string" ? metadata.status === "running"
                : native.background || /working in the background/i.test(result)
              if (child && child !== data.sessionID) {
                emit({ type: "helper-created", sessionID: child, parentSessionID: data.sessionID, ...native.identity })
                const spawned = spawnModels.get(callID)
                if (spawned && !helperModels.has(child)) helperModels.set(child, { ...spawned, parent: data.sessionID })
                if (background) backgroundHelpers.add(child)
              }
              spawnModels.delete(callID)
              if (!background) emit(reviewEvent(data.sessionID, callID, native.identity, result, root))
            }
            const created = spawn ? bbSpawnEvent(data.sessionID, spawn, result) : null
            emit(created)
            if (created && spawnPins.has(callID))
              emit({ type: "helper-agent", sessionID: created.sessionID, parentSessionID: data.sessionID, agent: spawnPins.get(callID) })
            if (read) emit(bbReadEvent(state, read, result, root))
            const stamp = bbStamps.get(callID)
            if (stamp?.project && stampSucceeded(result)) projectPins.set(data.sessionID, stamp)
            else if (stamp?.thread) {
              const pin = bbPinEvent(state, data.sessionID, stamp, result)
              if (pin) emit(pin)
              else logFailure("BB agent pin not verified (unknown helper, role differs from its brief, or the RPC failed)", new Error("unverified pin"))
              mismatch(data.sessionID, stamp.thread, state.helpers.get(stamp.thread)?.role ?? "", stamp.agent)
            }
            forget(callID)
          }
        } catch (error) { logFailure("event handling", error) }
      }
    })().catch((error) => logFailure("event subscription", error))

    await ctx.skill.transform((editor) => {
      const content = readFileSync(skillPath, "utf8")
      editor.remove("hivecall")
      editor.add({ id: "hivecall", name: "Hivecall", description: "Run a user-authorized multi-agent ledger workflow", path: skillPath, content })
    })

    // The orchestrator types ledger and run-card changes through these tools instead of one-off scripts (invariant 5: it
    // decides the content; the tool checks the proof first, writes one fixed format, fails loudly, and knows its caller).
    const toolText = (path: string) => existsSync(path) ? readFileSync(path, "utf8") : ""
    const orchestratorOnly = (sessionID: string) => {
      if (!existsSync(cardPath)) throw new Error("No hivecall run card (.hivecall/run.md) here; these tools work only inside a run.")
      if (!isOrchestrator(sessionID)) throw new Error("Only the run's orchestrator edits the ledger and run card; report the result to it instead.")
    }
    const ledgerSchema = { type: "object", additionalProperties: false, required: ["action", "id"], properties: {
      action: { type: "string", enum: ["tick", "fail", "park", "add"] }, id: { type: "string", description: "Item id, e.g. ISC-12" },
      observed: { type: "string", description: "tick: what the verifier saw" }, evidence: { type: "string", description: "Existing evidence file path" },
      commit: { type: "string", description: "Commit id the result is about" }, verifier: { type: "string", description: "Who verified (helper name or session)" },
      canary: { type: "string", description: "tick: known-broken case that still fails, when the commit edits the item's own check" },
      reason: { type: "string", description: "fail/park: why" }, unlock: { type: "string", description: "park: what unblocks it" },
      text: { type: "string", description: "add: observable behavior — check: exact check" }, feature: { type: "string", description: "add: existing feature heading" } } }
    const cardSchema = { type: "object", additionalProperties: false, required: ["action"], properties: {
      action: { type: "string", enum: ["status", "note"] }, status: { type: "string", enum: ["running", "waiting-owner", "waiting-usage", "closed"] },
      section: { type: "string", description: "note: run-card section heading without ##, e.g. Lessons, Answers, Final report" },
      text: { type: "string", description: "note: the line(s) to append to that section" } } }
    await ctx.tool.transform?.((editor) => {
      editor.add({
        name: "hivecall_ledger",
        description: "Hivecall orchestrator only: tick, fail, park or add one checklist item. A tick is refused unless it would count (verified approval, existing commit and evidence file).",
        input: ledgerSchema,
        execute: async (input: unknown, context: { sessionID: string }) => {
          orchestratorOnly(context.sessionID)
          const edit = input as LedgerEdit
          const path = activeLedger(root), before = toolText(path)
          const result = editLedger(before, edit)
          if ("error" in result) throw new Error(`hivecall_ledger: ${result.error}. Nothing was written.`)
          const id = iscId(edit.id)
          const problems = edit.action === "tick" ? tickProblems(result.text, id, state.approvals, state.grandfathered, root) : []
          if (problems.length) throw new Error(`hivecall_ledger: ${id} would not count, so it was not ticked: ${problems.join("; ")}.`)
          writeFileSync(path, result.text)
          if (edit.action === "tick") tickedBy.set(id, context.sessionID)
          observeLedger(context.sessionID)
          record({ type: "ledger-tool", action: edit.action, id, sessionID: context.sessionID })
          return { content: `${edit.action} ${id} written to ${relative(root, path) || path}.` }
        },
      })
      editor.add({
        name: "hivecall_card",
        description: "Hivecall orchestrator only: set the run card status, or append a line to one of its sections. Closing is gated like any run-card write.",
        input: cardSchema,
        execute: async (input: unknown, context: { sessionID: string }) => {
          orchestratorOnly(context.sessionID)
          const result = editCard(toolText(cardPath), input as CardEdit)
          if ("error" in result) throw new Error(`hivecall_card: ${result.error}. Nothing was written.`)
          writeFileSync(cardPath, result.text)
          return { content: "Run card updated." }
        },
      })
    })

    await ctx.command.transform((editor) => {
      editor.add({
        name: "hivecall",
        description: "Start the explicitly invoked Hivecall workflow",
        execute: async ({ sessionID, prompt, delivery }) => {
          await ctx.session.prompt({ ...prompt, sessionID,
            text: `Load and follow the hivecall skill for this explicitly invoked request.\n\n${prompt.text}`,
            delivery })
        },
      })
    })

    await ctx.session.hook("context", (event) => {
      if (activeRun(root)) event.system.push({ type: "text", text: anchor(root) })
    })

    // Observe only: BB delivers child lifecycle notices to the parent session as prompts.
    await ctx.session.hook("prompt", (event) => {
      try {
        const text = String(event.prompt?.text ?? "")
        // A session's first prompt is its brief when it carries a TALK-BACK block.
        if (!sessionRoles.has(event.sessionID)) sessionRoles.set(event.sessionID, /talk[- ]?back/i.test(text) ? briefRole(text) : "")
        for (const notice of bbNoticeEvents(state, event.sessionID, text, root)) emit(notice)
      } catch (error) { logFailure("prompt hook", error) }
    })

    await ctx.tool.hook("execute.before", (event) => {
      let violation: Violation | null = null, modelViolation: Violation | null = null
      const callID = `${event.sessionID}:${event.id}`
      try { observeLedger() } catch (error) { logFailure("ledger observation", error) }
      inFlight.set(callID, event.sessionID)
      try {
        const input = event.input && typeof event.input === "object" ? event.input as Record<string, unknown> : {}
        if (event.tool === "skill" && typeof input.id === "string") skillCalls.set(callID, input.id)
        if (event.tool === "skill" && input.id === "hivecall") arm(event.sessionID)
        if (!live()) return
        startRun()
        const projectPin = projectPins.get(event.sessionID)
        projectPins.delete(event.sessionID)
        if (event.tool === "subagent") {
          // Fill a missing TALK-BACK block or PROMISE line rather than block the spawn; the orchestrator is told.
          const brief = fillBrief(String(input.prompt ?? ""), event.sessionID)
          if (brief.filled.length) {
            input.prompt = brief.prompt
            event.input = input
            record({ type: "brief-filled", sessionID: event.sessionID, filled: brief.filled.join(",") })
            warnings.push(`Added a default ${brief.filled.join(" and ")} to the brief "${String(input.description ?? "").slice(0, 60)}".` +
              (brief.filled.includes("PROMISE") ? " Its PROMISE rows=- claims no items, so a qa PASS from it cannot tick anything; name the rows in the next brief." : ""))
          }
          const identity = helperIdentity(input)
          toolCalls.set(callID, { identity, background: input.background === true })
          mismatch(event.sessionID, callID, identity.role, identity.agent)
          // Model policy from the run card (P5): fill the agent's model when none is passed; pause once on an off-list one.
          const policy = modelPolicy(existsSync(cardPath) ? readFileSync(cardPath, "utf8") : "")
          const agent = identity.agent
          let model = typeof input.model === "string" ? input.model : ""
          if (!model && policy.primary.get(agent)) {
            model = policy.primary.get(agent)!
            input.model = model
            event.input = input
            record({ type: "model-filled", sessionID: event.sessionID, agent, model })
          }
          const allowed = allowedModels(policy, agent)
          if (model && !allowed.includes(model)) modelViolation = { id: "model-policy", key: `model-policy:${agent}:${model}`, cap: 1, message: "",
            detail: allowed.length ? `${agent} may run on ${allowed.join(" or ")} (run card models: / backup models:)` : `the run card names no model for ${agent}` }
          if (model) spawnModels.set(callID, { agent, model })
          // The judge should not share the builder's model (P7): warn when qa or a reviewer runs on a model a builder used for its items.
          const items = [...new Set([...(identity.promise ?? "").split(","), ...identity.rows.split(",")].filter(Boolean))]
          if (model && /^(?:build|code|general)$/.test(agent)) for (const item of items) builderModels.set(item, (builderModels.get(item) ?? new Set()).add(model))
          const shared = model && (agent === "qa" || agent === "reviewer") ? items.filter((item) => builderModels.get(item)?.has(model)) : []
          if (shared.length && !warned.has(key(event.sessionID, `same-model:${agent}:${shared.join(",")}`))) {
            warned.add(key(event.sessionID, `same-model:${agent}:${shared.join(",")}`))
            record({ type: "warning", rule: `same-model:${agent}:${shared.join(",")}`, sessionID: event.sessionID })
            warnings.push(`${agent} for ${shared.join(", ")} runs on ${model}, the model that built ${shared.length === 1 ? "it" : "them"}; an independent judge should use another model from the run card.`)
          }
        }
        const command = event.tool === "shell" ? String(input.command ?? "") : ""
        const cwd = typeof input.workdir === "string" ? resolve(root, input.workdir) : root
        const normalized = command ? shellDelegation(command, cwd) : null
        if (normalized?.warning) logFailure(normalized.warning, new Error("parse failed"))
        // Track every single BB spawn, gated or not, so its real result can be attributed; only a parsed brief role can be pinned.
        const spawnIdentity = normalized?.kind === "spawn" ? normalized.call ? helperIdentity(normalized.call.input) : { agent: "", role: "", slice: "", rows: "" } : null
        if (spawnIdentity) bbSpawns.set(callID, spawnIdentity)
        if (spawnIdentity?.role && projectPin && projectPin.project === normalized?.project && projectPin.agent === spawnIdentity.role)
          spawnPins.set(callID, projectPin.agent)
        const read = command ? bbOutputRead(command) : null
        if (read) bbReads.set(callID, read)
        const pin = command ? bbAgentStamp(command) : {}
        if (pin.warning) logFailure(pin.warning, new Error("unverified pin"))
        if (pin.stamp) bbStamps.set(callID, pin.stamp)
        // A card tool call is gated as the run-card write it makes.
        const cardEdit = event.tool === "hivecall_card" ? editCard(existsSync(cardPath) ? readFileSync(cardPath, "utf8") : "", input as CardEdit) : null
        const policyCall = normalized?.call ?? (cardEdit && "text" in cardEdit ? { tool: "write", input: { path: ".hivecall/run.md", content: cardEdit.text } as Record<string, unknown> }
          : { tool: event.tool, input })
        const target = policyCall.input.sessionID
        if (normalized?.kind === "tell" && typeof target === "string" && !state.finished.has(target))
          policyCall.input.sessionID = bbHelperSession(state, event.sessionID, target) ?? target
        const call = { ...policyCall, sessionID: event.sessionID }
        // One decision line per spawn (ticks are logged after the call); a BB delegation the hook cannot read is logged as ungated.
        if (normalized?.kind && !normalized.call) record({ type: "allowed", action: normalized.kind, sessionID: event.sessionID, ungated: 1 })
        const action = call.tool === "subagent" ? normalized?.kind ?? "spawn" : undefined
        violation = ruleFor(call, state, root) ?? modelViolation
        const blockKey = violation ? violation.key ?? violation.id : ""
        const decision = violation ? blockDecision(state, event.sessionID, blockKey, violation.cap) : null
        if (decision && violation?.hold && !decision.block) { decision.block = true; decision.count += 1 }
        if (!violation || !decision?.block) {
          if (action) record({ type: "allowed", action, sessionID: event.sessionID, rule: violation?.id })
          if (violation) warnOnce(event.sessionID, blockKey)
          if (action === "spawn" || action === "tell") {
            // A valid RE-PLAN in the brief is the reflection; it resets that item's hill-climb count.
            for (const replan of replanEvents(call.input, state, root)) emit({ ...replan, sessionID: event.sessionID })
            const identity = helperIdentity(call.input)
            const dirty = identity.agent.includes("qa") || identity.role === "qa" ? dirtyFiles(root) : []
            const mark = dirty.join(",")
            if (dirty.length && !warned.has(key(event.sessionID, `qa-dirty:${mark}`))) {
              warned.add(key(event.sessionID, `qa-dirty:${mark}`))
              record({ type: "warning", rule: `qa-dirty:${mark}`, sessionID: event.sessionID })
              warnings.push(`qa started while the checkout has uncommitted edits (${dirty.slice(0, 5).join(", ")}${dirty.length > 5 ? ", ..." : ""}). ${rules.find((r) => r.id === "qa-dirty")?.message ?? ""}`)
            }
          }
          return
        }
        record({ type: "blocked", rule: blockKey, sessionID: event.sessionID, tool: event.tool, count: decision.count, action })
      } catch (error) {
        logFailure("tool hook", error)
        return
      }
      if (violation) {
        inFlight.delete(callID)
        throw new Error([rules.find((rule) => rule.id === violation?.id)?.message || violation.message, violation.detail && `(${violation.detail})`].filter(Boolean).join(" "))
      }
    })

    // Tick check: after every call while the run card is (or just was) active, judge the ledger as it now stands. A tick
    // without approval and receipt is logged once and does not count; the orchestrator is told and cannot close the run
    // until it is earned or unticked. The ledger and run card are never changed.
    // `closer` is the session blamed for a run-card close seen now (the one session with calls in flight, else "unknown").
    const judge = (closer: string) => {
      if (!existsSync(resolve(runDir, "run.md"))) return
      const active = activeRun(root)
      if (!active && !wasActive) return
      startRun()
      const ledger = activeLedger(root)
      const text = existsSync(ledger) ? readFileSync(ledger, "utf8") : ""
      const bad = new Set(unearned(text, state.approvals, state.grandfathered, root))
      const canary = new Set(canaryMissing(text, root))
      const ticked = new Set(tickedItems(text))
      const by = (id: string) => tickedBy.get(id) ?? "unknown"
      for (const id of bad) if (!flagged.has(id)) {
        flagged.add(id)
        record({ type: "tick-unearned", rule: "tick-gate", id, sessionID: by(id) })
        notices.push(canary.has(id) ? `${id}'s commit edits a file its own check names, and its receipt has no CANARY: line showing a known-broken case still fails, so it does not count.`
          : `${id} is ticked without a verified reviewer APPROVE_CODE, APPROVE_PLAN or SELECTED, or qa REPRODUCED for Discovery items only, or a qa PASS naming its commit when that commit only renames files or changes tests or docs on a proven parent, and its receipt, so it does not count.`)
      }
      for (const id of [...flagged]) if (!bad.has(id)) flagged.delete(id)
      for (const id of [...earned]) if (!ticked.has(id)) earned.delete(id)
      for (const id of ticked) if (!bad.has(id) && !state.grandfathered.has(id) && !earned.has(id)) {
        earned.add(id)
        const row = { type: "allowed", action: "tick", id, sessionID: by(id) }
        apply(state, row) // a new earned tick restarts the run-wide hill-climb count
        record(row)
      }
      if (active) {
        wasActive = true
        if (Date.now() - archivedAt > 10 * 60_000) archive()
      } else {
        wasActive = false
        archive()
        if (bad.size) {
          record({ type: "close-unearned", rule: "no-early-done", ids: [...bad].join(","), sessionID: closer })
          notices.push(`The run card was closed while ${[...bad].join(", ")} ${bad.size === 1 ? "is" : "are"} ticked without approval and receipt; the close does not count them.`)
        }
      }
    }
    await ctx.tool.hook("execute.after", (event) => {
      const callID = `${event.sessionID}:${(event as { id?: string }).id ?? ""}`
      try { observeLedger() } catch (error) { logFailure("ledger observation", error) }
      const closer = inFlightActor()
      inFlight.delete(callID)
      try { judge(closer) } catch (error) { logFailure("tick check", error) }
      try {
        // On the orchestrator's own completed call the notice rides on its result; otherwise it is sent at once (flush).
        if ((notices.length || warnings.length) && event.status === "completed" && isOrchestrator(event.sessionID)) {
          event.result = { ...event.result, content: [...(event.result?.content ?? []), { type: "text", text: outbox() }] }
        } else flush(event.sessionID)
      } catch (error) { logFailure("tick check", error) }
    })

    return () => controller.abort()
  },
})
