import { Plugin } from "@opencode/plugin"
import { anchorText, bb, gateStatus } from "./bb"
import { type Gate, SEND_BACK_LIMIT, ending, freshReceipts, git, log, missing, missionLaunch, qaVerdict, resultBody, reviewDecision, snapshot, wrongAgent } from "./gate"
import { statSync } from "node:fs"

export * from "./gate"
export * from "./bb"

/**
 * Four jobs only:
 * 1. Done gate: a small Mission (first prompt line `MISSION: SMALL`) must end its report with an honest ending line,
 *    `ENDING: DONE | BLOCKED | NEEDS DECISION | UNVERIFIED`. DONE (or no ending) without a fresh reviewer `APPROVE_CODE`
 *    and then a fresh qa `PASS` started after that approval is sent back, naming what is missing. Only the child's own
 *    result body is read, never the envelope that echoes the parent's description. A verdict counts only while the worktree
 *    still matches the snapshot taken when that subagent started, so a change by any route (edit tool, shell) voids it.
 *    A qa PASS also needs proof: it must name at least one receipt file (screenshot, log, report, output) that exists,
 *    is not empty, and was written after that qa subagent started. After the last send-back the gate tells the root
 *    Supervisor to treat the Mission as BLOCKED.
 * 2. Right agent: inside any Mission, a helper whose brief names a role (build, reviewer, qa, research) but would run
 *    as another agent is refused, and the root is told when a Mission itself runs as the wrong agent.
 * 3. Re-anchor: every `bb-supervisor` request carries its role, active Missions with their gate status, and Task cards,
 *    read from BB state, so the root keeps them after compaction.
 * 4. Launch guard: refuse a Supervisor's BB Mission spawn when its brief has no TALK-BACK: line.
 */

export default Plugin.define({
  id: "bb-supervisor",
  async setup(ctx) {
    const gates = new Map<string, Gate>() // small Missions, by session
    const missions = new Map<string, string>() // every Mission session -> the agent its brief requires
    const agents = new Map<string, string>() // session -> agent it runs as
    const seen = new Set<string>() // sessions whose first prompt was checked
    const wrong = new Map<string, string>() // Mission session -> the wrong agent it ran as (the root was told once)
    const dir = ctx.location?.directory ?? process.cwd()
    type Call = { agent: string; at: string; started: number; description: string } // a fresh gate subagent, the worktree snapshot and time when it started
    const calls = new Map<string, Call>() // `${session}:${call}`
    const children = new Map<string, Call & { parent: string }>() // background subagent session

    const verdict = (parent: string, call: Call, raw: string) => {
      const gate = gates.get(parent)
      const text = resultBody(raw, call.description)
      if (!gate || !call.at || text === null) return // an unrecognised envelope is no verdict
      if (call.agent === "reviewer") {
        const decision = reviewDecision(text) // only an overall APPROVE_CODE approves; REVISE_CODE or ASK_USER withdraws approval
        if (decision && decision !== "APPROVE_CODE") { gate.approvedAt = null; gate.passedAt = null }
        else if (decision) { gate.approvedAt = call.at; gate.approvedTime = Date.now(); gate.passedAt = null; gate.proof = {} } // QA must follow this approval
      }
      if (call.agent === "qa") {
        const afterApproval = gate.approvedAt === call.at && call.started > gate.approvedTime
        const pass = qaVerdict(text) === "PASS" && afterApproval
        const receipts = pass ? freshReceipts(text, dir, call.started, call.at) : []
        gate.receipts = [...new Set([...gate.receipts, ...receipts])]
        gate.passedAt = receipts.length ? call.at : null
        gate.proof = Object.fromEntries(receipts.map((f) => [f, git(dir, ["hash-object", f]) ?? ""]))
        gate.qaNote = qaVerdict(text) === "PASS" && !afterApproval ? "the last qa run started before the current approval, so it does not count"
          : pass && !receipts.length ? "the last qa PASS named no receipt file written during its run, so it does not count" : ""
      }
      save(parent)
    }
    const textOf = (content: unknown) => Array.isArray(content)
      ? content.map((part) => part && typeof part === "object" && "text" in part ? String(part.text) : "").join("\n") : String(content ?? "")
    // A Mission running as the wrong agent: the root hears it once, and a small Mission cannot end DONE.
    const checkMission = (sessionID: string) => {
      const want = missions.get(sessionID), have = agents.get(sessionID)
      if (!want || !have || have === want || wrong.has(sessionID)) return
      wrong.set(sessionID, have)
      const gate = gates.get(sessionID)
      if (gate) gate.wrongAgent = have
      save(sessionID)
      const mission = bb.mission(sessionID)
      if (!mission || !bb.tell(mission.parent, `[bb-supervisor] @thread:${mission.id} runs as \`${have}\`, but its brief needs \`${want}\`. ` +
        `Its work does not count; stop it and spawn it again as \`${want}\`.`)) log("wrong-agent notice to the root", new Error("no parent thread or bb thread tell failed"))
    }

    // Gate status survives plugin reloads and server restarts: written through to plugin storage, reloaded at setup.
    const setStatus = (sessionID: string, text: string) => {
      gateStatus.set(sessionID, text)
      void Promise.resolve(ctx.storage?.set(`gate/${sessionID}`, text)).catch((error) => log("gate status save", error))
    }
    // The Mission's identity, gate and send-back count survive too, so a resumed Mission stays gated.
    function save(sessionID: string) {
      const kind = missions.get(sessionID)
      if (!kind) return
      void Promise.resolve(ctx.storage?.set(`mission/${sessionID}`, { kind, gate: gates.get(sessionID) ?? null, wrong: wrong.get(sessionID) ?? null })).catch((error) => log("Mission state save", error))
    }
    const load = async (prefix: string, use: (session: string, value: unknown) => void) => {
      try {
        for (let after: string | undefined, page; (page = await ctx.storage?.scan({ prefix, after, limit: 500 })); after = page.next) {
          for (const { key, value } of page.entries) use(key.slice(prefix.length), value)
          if (!page.next) break
        }
      } catch (error) { log(`${prefix} load`, error) }
    }
    await load("gate/", (session, value) => typeof value === "string" && gateStatus.set(session, value))
    await load("mission/", (session, value) => {
      const saved = value as { kind?: string; gate?: Gate | null; wrong?: string | null } | null
      if (!saved?.kind) return
      missions.set(session, saved.kind)
      seen.add(session)
      if (saved.gate) gates.set(session, saved.gate)
      if (saved.wrong) wrong.set(session, saved.wrong)
    })
    // Acceptance is rechecked against the files and receipts whenever it is read.
    const intact = (gate: Gate) => Object.entries(gate.proof).every(([f, hash]) => {
      try { return statSync(f).size > 0 && git(dir, ["hash-object", f]) === hash } catch { return false }
    })
    const statusOf = (sessionID: string) => {
      const text = gateStatus.get(sessionID), gate = gates.get(sessionID)
      if (!text?.startsWith("DONE accepted")) return text
      if (!gate) return "not done: its acceptance cannot be rechecked (no gate record), so it does not count"
      return intact(gate) && !gate.wrongAgent && !missing(gate, snapshot(dir, gate.receipts)).length ? text
        : "not done: files or the receipt changed after it was accepted"
    }

    const controller = new AbortController()
    void (async () => {
      for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
        try {
          const data = (event as { data?: Record<string, unknown> }).data ?? {}
          const sessionID = typeof data.sessionID === "string" ? data.sessionID : ""
          if ((event.type === "session.created" || event.type === "session.agent.selected") && sessionID && typeof data.agent === "string") {
            agents.set(sessionID, data.agent.toLowerCase())
            checkMission(sessionID)
          }
          if (event.type === "session.text.ended" && gates.has(sessionID)) gates.get(sessionID)!.lastText = String(data.text ?? "")
          if ((event.type === "session.tool.success" || event.type === "session.tool.failed") && typeof data.id === "string") {
            const call = calls.get(`${sessionID}:${data.id}`)
            calls.delete(`${sessionID}:${data.id}`)
            if (!call || event.type === "session.tool.failed") continue
            const metadata = data.metadata && typeof data.metadata === "object" ? data.metadata as Record<string, unknown> : {}
            const child = typeof metadata.sessionID === "string" ? metadata.sessionID : ""
            if (metadata.status === "running" && child) children.set(child, { ...call, parent: sessionID })
            else verdict(sessionID, call, textOf(data.content))
          }
          // A background subagent's result reaches its parent as a synthetic inbox item; a failed or cancelled one just ends.
          const item = data.item && typeof data.item === "object" ? data.item as Record<string, unknown> : {}
          const payload = event.type === "session.inbox.enqueued" && item.type === "synthetic" && item.payload && typeof item.payload === "object"
            ? item.payload as Record<string, unknown> : null
          const metadata = payload?.metadata && typeof payload.metadata === "object" ? payload.metadata as Record<string, unknown> : {}
          const child = children.get(String(metadata.childID ?? ""))
          if (child && metadata.source === "subagent" && metadata.state !== "running" && child.parent === sessionID) {
            children.delete(String(metadata.childID))
            if (metadata.state === "completed") verdict(sessionID, { ...child, description: String(payload?.description ?? child.description) }, String(payload?.text ?? ""))
          }
          if (event.type === "session.deleted") { calls.forEach((_, k) => k.startsWith(`${sessionID}:`) && calls.delete(k)); children.delete(sessionID) }
          // Done gate: the Mission ended a turn. BLOCKED, NEEDS DECISION and UNVERIFIED are honest endings and pass;
          // DONE, or no ending at all, needs both gates.
          if (event.type === "session.execution.succeeded" && gates.has(sessionID)) {
            const gate = gates.get(sessionID)!
            const pending = [...children.values()].some((c) => c.parent === sessionID) || [...calls.keys()].some((k) => k.startsWith(`${sessionID}:`))
            if (pending) continue
            const said = ending(gate.lastText)
            if (said && said !== "DONE") { setStatus(sessionID, `${said} (honest ending, not done)`); continue }
            if (gate.passedAt && !intact(gate)) { gate.passedAt = null; gate.qaNote = "its receipt file was deleted or changed after the PASS" }
            const gaps = [...(gate.wrongAgent ? [`a Mission running as build (it runs as ${gate.wrongAgent})`] : []), ...missing(gate, snapshot(dir, gate.receipts)),
              ...(said ? [] : ["a first report line `ENDING: DONE`, `ENDING: BLOCKED`, `ENDING: NEEDS DECISION` or `ENDING: UNVERIFIED`"])]
            if (!gaps.length) { setStatus(sessionID, "DONE accepted (fresh review, fresh QA, receipt intact)"); save(sessionID); continue }
            setStatus(sessionID, `not done: still needs ${gaps.join(" and ")}`)
            if (gate.sentBack >= SEND_BACK_LIMIT) {
              // Out of send-backs: the root hears it from the gate, not from the Mission's own report.
              setStatus(sessionID, `BLOCKED by the done gate after ${SEND_BACK_LIMIT} send-backs: still needs ${gaps.join(" and ")}`)
              const mission = gate.escalated ? null : bb.mission(sessionID)
              if (mission && bb.tell(mission.parent, `[bb-supervisor done gate] @thread:${mission.id} ended without ${gaps.join(" and ")} after ` +
                `${SEND_BACK_LIMIT} send-backs. Treat it as BLOCKED, not done.`)) gate.escalated = true
              else if (!gate.escalated) log("BLOCKED notice to the root", new Error("no parent thread or bb thread tell failed"))
              save(sessionID)
              continue
            }
            gate.sentBack++
            save(sessionID)
            await ctx.session.prompt({ sessionID, text: `[bb-supervisor done gate] Not done yet: this small Mission still needs ${gaps.join(" and ")}. ` +
              "Run any missing gate as a new subagent (reviewer with code-quality-gate, then a new qa with verification-gate started after that approval; qa must write its proof to a receipt file and name that file's path in its result), then report again. " +
              `If you cannot, start your report with ENDING: BLOCKED, ENDING: NEEDS DECISION or ENDING: UNVERIFIED and say why. (send-back ${gate.sentBack}/${SEND_BACK_LIMIT})` })
          }
        } catch (error) { log("event handling", error) }
      }
    })().catch((error) => log("event subscription", error))

    await ctx.session.hook("prompt", (event) => {
      if (seen.has(event.sessionID)) return
      seen.add(event.sessionID)
      // Only the brief's first line counts, so a subagent handed a copy of the brief is never gated.
      const kind = /^\s*MISSION:\s*(SMALL|LARGE)\b/i.exec(String(event.prompt?.text ?? ""))?.[1]?.toUpperCase()
      if (!kind) return
      missions.set(event.sessionID, kind === "SMALL" ? "build" : "orchestrator")
      if (kind === "SMALL") gates.set(event.sessionID, { approvedAt: null, approvedTime: 0, passedAt: null, receipts: [], proof: {}, sentBack: 0, escalated: false, lastText: "", qaNote: "", wrongAgent: "" })
      save(event.sessionID)
      checkMission(event.sessionID)
    })

    await ctx.tool.hook("execute.before", (event) => {
      const input = event.input && typeof event.input === "object" ? event.input as Record<string, unknown> : {}
      if (event.agent === "bb-supervisor" && (event.tool === "shell" || event.tool === "bash")) {
        const refusal = missionLaunch(String(input.command ?? ""), String(input.workdir ?? dir))
        if (refusal) throw new Error(refusal)
      }
      if (event.tool !== "subagent" || !missions.has(event.sessionID) && !gates.has(event.sessionID)) return
      const refusal = wrongAgent(input)
      if (refusal) throw new Error(refusal)
      const agent = String(input.agent ?? "").toLowerCase()
      if (!gates.has(event.sessionID)) return
      // Every helper counts as pending until it ends; only a new reviewer or qa (not one continued by sessionID) is a gate.
      const gate = (agent === "reviewer" || agent === "qa") && !input.sessionID
      calls.set(`${event.sessionID}:${event.id}`, { agent, at: gate ? snapshot(dir, gates.get(event.sessionID)!.receipts) : "", started: Date.now(), description: String(input.description ?? "") })
    })

    await ctx.session.hook("context", (event) => {
      if (event.agent !== "bb-supervisor") return
      const text = anchorText(event.sessionID, undefined, statusOf)
      if (text) event.system.push({ type: "text", text })
    })

    return () => controller.abort()
  },
})
