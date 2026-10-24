import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"
import { bbAgentStamp, bbHelperSession, bbNoticeEvents, bbOutputRead, bbPinEvent, bbReadEvent, bbSpawnEvent, shellDelegation, stampSucceeded, type BbStamp } from "./watchdog/adapters"
import { activeLedger, activeRun, agentMismatch, anchor, apply, blockDecision, briefRole, helperIdentity, memory, reviewEvent, ruleFor, tickedItems, unearned, type HiveEvent } from "./watchdog/policy"

const pluginDir = dirname(fileURLToPath(import.meta.url))
const skillPath = resolve(pluginDir, "SKILL.md")
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
    const pendingCalls = [skillCalls, toolCalls, bbSpawns, bbReads, bbStamps, spawnPins]
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
    const flagged = new Set<string>(), earned = new Set<string>() // ids already logged as unearned / earned
    const notices: string[] = [] // waiting for the orchestrator's next completed call
    let wasActive = activeRun(root)
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
      if (!activeRun(root) && (started || state.approvals.size)) { // a fresh run: forget the last run's tick state
        state.approvals.clear(); state.grandfathered.clear(); started = false; orchestrators.clear(); flagged.clear(); earned.clear()
      }
      if (sessionID && !orchestrators.has(sessionID)) orchestrators.add(sessionID)
      save()
    }

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
          if (event.type === "session.created" && typeof data.sessionID === "string" && typeof data.parentID === "string") {
            childParents.set(data.sessionID, data.parentID)
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
            if (body !== null) emit(reviewEvent(helper.parentSessionID, childID, helper, body))
            else if (metadata.state === "completed") logFailure("background helper result envelope not recognised", new Error("unrecognised envelope"))
          }
          if (event.type === "session.tool.failed" && typeof data.sessionID === "string" && typeof data.id === "string") forget(`${data.sessionID}:${data.id}`)
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
                if (background) backgroundHelpers.add(child)
              }
              if (!background) emit(reviewEvent(data.sessionID, callID, native.identity, result))
            }
            const created = spawn ? bbSpawnEvent(data.sessionID, spawn, result) : null
            emit(created)
            if (created && spawnPins.has(callID))
              emit({ type: "helper-agent", sessionID: created.sessionID, parentSessionID: data.sessionID, agent: spawnPins.get(callID) })
            if (read) emit(bbReadEvent(state, read, result))
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
        for (const notice of bbNoticeEvents(state, event.sessionID, text)) emit(notice)
      } catch (error) { logFailure("prompt hook", error) }
    })

    await ctx.tool.hook("execute.before", (event) => {
      let violation: { id: string; message: string } | null = null
      const callID = `${event.sessionID}:${event.id}`
      try {
        const input = event.input && typeof event.input === "object" ? event.input as Record<string, unknown> : {}
        if (event.tool === "skill" && typeof input.id === "string") skillCalls.set(callID, input.id)
        if (event.tool === "skill" && input.id === "hivecall") arm(event.sessionID)
        if (!live()) return
        startRun()
        const projectPin = projectPins.get(event.sessionID)
        projectPins.delete(event.sessionID)
        if (event.tool === "subagent") {
          const identity = helperIdentity(input)
          toolCalls.set(callID, { identity, background: input.background === true })
          mismatch(event.sessionID, callID, identity.role, identity.agent)
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
        const policyCall = normalized?.call ?? { tool: event.tool, input }
        const target = policyCall.input.sessionID
        if (normalized?.kind === "tell" && typeof target === "string" && !state.finished.has(target))
          policyCall.input.sessionID = bbHelperSession(state, event.sessionID, target) ?? target
        const call = { ...policyCall, sessionID: event.sessionID }
        // One decision line per spawn (ticks are logged after the call); a BB delegation the hook cannot read is logged as ungated.
        if (normalized?.kind && !normalized.call) record({ type: "allowed", action: normalized.kind, sessionID: event.sessionID, ungated: 1 })
        const action = call.tool === "subagent" ? normalized?.kind ?? "spawn" : undefined
        violation = ruleFor(call, state, root)
        const decision = violation ? blockDecision(state, event.sessionID, violation.id) : null
        if (!violation || !decision?.block) {
          if (action) record({ type: "allowed", action, sessionID: event.sessionID, rule: violation?.id })
          if (violation) warnOnce(event.sessionID, violation.id)
          return
        }
        record({ type: "blocked", rule: violation.id, sessionID: event.sessionID, tool: event.tool, count: decision.count, action })
      } catch (error) {
        logFailure("tool hook", error)
        return
      }
      if (violation) {
        throw new Error([rules.find((rule) => rule.id === violation?.id)?.message ?? violation.message, violation.detail && `(${violation.detail})`].filter(Boolean).join(" "))
      }
    })

    // Tick check: after every call while the run card is (or just was) active, judge the ledger as it now stands. A tick
    // without approval and receipt is logged once and does not count; the orchestrator is told and cannot close the run
    // until it is earned or unticked. The ledger and run card are never changed.
    const judge = (event: { sessionID: string; tool: string }) => {
      if (!existsSync(resolve(runDir, "run.md"))) return
      const active = activeRun(root)
      if (!active && !wasActive) return
      startRun()
      const ledger = activeLedger(root)
      const text = existsSync(ledger) ? readFileSync(ledger, "utf8") : ""
      const bad = new Set(unearned(text, state.approvals, state.grandfathered, root))
      const ticked = new Set(tickedItems(text))
      const tool = event.tool
      for (const id of bad) if (!flagged.has(id)) {
        flagged.add(id)
        record({ type: "tick-unearned", rule: "tick-gate", id, sessionID: event.sessionID, tool })
        notices.push(`${id} is ticked without a verified reviewer approval and its receipt, so it does not count.`)
      }
      for (const id of [...flagged]) if (!bad.has(id)) flagged.delete(id)
      for (const id of [...earned]) if (!ticked.has(id)) earned.delete(id)
      for (const id of ticked) if (!bad.has(id) && !state.grandfathered.has(id) && !earned.has(id)) {
        earned.add(id)
        record({ type: "allowed", action: "tick", id, sessionID: event.sessionID, tool })
      }
      if (active) wasActive = true
      else {
        wasActive = false
        if (bad.size) {
          record({ type: "close-unearned", rule: "no-early-done", ids: [...bad].join(","), sessionID: event.sessionID, tool })
          notices.push(`The run card was closed while ${[...bad].join(", ")} ${bad.size === 1 ? "is" : "are"} ticked without approval and receipt; the close does not count them.`)
        }
      }
    }
    await ctx.tool.hook("execute.after", (event) => {
      try { judge(event) } catch (error) { logFailure("tick check", error) }
      try {
        // Delivered whenever the orchestrator next completes a call, even after the run card closed.
        if (notices.length && event.status === "completed" && isOrchestrator(event.sessionID)) {
          const rule = rules.find((r) => r.id === "tick-gate")?.message ?? ""
          event.result = { ...event.result, content: [...(event.result?.content ?? []), { type: "text", text: `[hivecall] ${notices.splice(0).join(" ")} ${rule}` }] }
        }
      } catch (error) { logFailure("tick check", error) }
    })

    return () => controller.abort()
  },
})
