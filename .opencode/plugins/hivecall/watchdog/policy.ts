import { existsSync, readFileSync } from "node:fs"
import { isAbsolute, resolve } from "node:path"
import { iscId, iscIds, parsePromise } from "./promise"

export { iscId, parsePromise, parsePromiseRows, promiseDefaults } from "./promise"

export function sliceKey(text: string): string | null {
  const explicit = text.match(/\bslice\s*=\s*([\w.-]+)/i)
  if (explicit) return /^ISC-\d+(?:\.\d+)*$/i.test(explicit[1]) ? iscId(explicit[1]) : explicit[1].toLowerCase()
  const ids = iscIds(text).sort()
  return ids.length ? ids.join(",") : null
}

/** Items a review brief asks about: PROMISE rows, else an explicit ISC slice, else every ISC id it names. */
export function reviewScope(text: string): string[] {
  const rows = parsePromise(text)?.rows
  if (rows?.size) return [...rows]
  const slice = sliceKey(text)
  return slice?.startsWith("ISC-") ? slice.split(",") : []
}

type Verdict = "approve" | "revise"

function verdictOf(text: string): Verdict | null {
  const approve = /\bAPPROVE_CODE\b/.test(text), revise = /\bREVISE_CODE\b/.test(text)
  return approve === revise ? null : approve ? "approve" : "revise"
}

/**
 * Reads a reviewer result. A `Decision:`/`Verdict:` line sets the overall verdict (else the only verdict used on lines naming no id);
 * a line naming ISC ids with one verdict sets those ids. Approval is per exact id inside the review scope.
 */
export function reviewOutcome(text: string, scope: string[]): { approved: string[]; revised: boolean } | null {
  const lines = text.split(/\r?\n/)
  const decision = lines.map((line) => /^\W*(?:decision|verdict)\b[^:=\n]*[:=].*?\b(APPROVE|REVISE)_CODE\b/i.exec(line)?.[1]).find(Boolean)
  const overall: Verdict | null = decision ? (decision.toUpperCase() === "APPROVE" ? "approve" : "revise")
    : verdictOf(lines.filter((line) => !iscIds(line).length).join("\n"))
  const perItem = new Map<string, Verdict>()
  for (const line of lines) {
    const verdict = verdictOf(line)
    if (verdict) for (const id of iscIds(line)) perItem.set(id, perItem.get(id) === "revise" ? "revise" : verdict)
  }
  if (!overall && !perItem.size) return null
  const approved = (scope.length ? scope : [...perItem.keys()]).filter((id) => (perItem.get(id) ?? overall) === "approve")
  return { approved, revised: overall === "revise" || (!overall && [...perItem.values()].includes("revise")) }
}

function discoveryOutcome(text: string, scope: string[], role: string): string[] {
  const approve = role === "qa" ? /\b(?:REPRODUCED|PASS)\b/ : /\b(?:APPROVE_PLAN|SELECTED)\b/
  const revise = role === "qa" ? /\b(?:NOT_REPRODUCED|BLOCKED|FAIL)\b/ : /\b(?:REVISE_PLAN|ASK_USER)\b/
  const verdict = (line: string): Verdict | null => {
    const yes = approve.test(line), no = revise.test(line)
    return yes === no ? null : yes ? "approve" : "revise"
  }
  const lines = text.split(/\r?\n/)
  // A negative on a line naming no ISC id vetoes every scoped id, even after an approving Decision/Result line.
  if (lines.some((line) => !iscIds(line).length && revise.test(line))) return []
  const token = role === "qa" ? "REPRODUCED|PASS|NOT_REPRODUCED|BLOCKED|FAIL" : "APPROVE_PLAN|SELECTED|REVISE_PLAN|ASK_USER"
  const decision = lines.map((line) => new RegExp(`^\\W*(?:[Dd][Ee][Cc][Ii][Ss][Ii][Oo][Nn]|[Vv][Ee][Rr][Dd][Ii][Cc][Tt]|[Ss][Tt][Aa][Tt][Uu][Ss]|[Rr][Ee][Ss][Uu][Ll][Tt])\\b[^:=\\n]*[:=].*?\\b(${token})\\b`).exec(line)?.[1]).find(Boolean)
  const overall = decision ? verdict(decision) : verdict(lines.filter((line) => !iscIds(line).length).join("\n"))
  const perItem = new Map<string, Verdict>()
  for (const line of lines) {
    const result = revise.test(line) ? "revise" : verdict(line)
    if (result) for (const id of iscIds(line)) perItem.set(id, perItem.get(id) === "revise" ? "revise" : result)
  }
  return scope.filter((id) => (perItem.get(id) ?? overall) === "approve")
}

/** Role a brief names for its helper: an `agent:`/`role:` line, `You are <Name> (<role>)`, or the one gate it says to run; "" if none. */
export function briefRole(text: string): string {
  const role = "(build|general|reviewer|qa|research)"
  const explicit = text.match(new RegExp(`^\\s*(?:agent|role)\\s*[:=]\\s*${role}\\b`, "im")) ??
    text.match(new RegExp(`\\bYou are \\w+ \\(${role}\\b`, "i"))
  if (explicit) return explicit[1].toLowerCase()
  const gates = new Set([...text.matchAll(/\b(?:run|use|load|follow)\s+(?:the\s+)?(?:skill\s+)?`?(code-quality-gate|verification-gate)\b/gi)]
    .map((match) => match[1].toLowerCase()))
  return gates.size === 1 ? (gates.has("code-quality-gate") ? "reviewer" : "qa") : ""
}

/** True when a brief names a role and the helper actually runs as a different agent. */
export function agentMismatch(role: string, agent: string): boolean {
  return Boolean(role && agent && !agent.toLowerCase().includes(role))
}

export type Helper = { parentSessionID: string; agent: string; role: string; slice: string; rows: string; promise?: string }

export type Memory = {
  blocks: Map<string, number>
  skills: Set<string>
  finished: Set<string>
  approvals: Set<string>
  /** Ticks already on the ledger when the run was first judged; they need no approval. */
  grandfathered: Set<string>
  revisions: Map<string, number>
  helpers: Map<string, Helper>
  reviewed: Set<string>
}

export function memory(): Memory {
  return { blocks: new Map(), skills: new Set(), finished: new Set(), approvals: new Set(), grandfathered: new Set(), revisions: new Map(),
    helpers: new Map(), reviewed: new Set() }
}

/** Neutral event rows (the `events.jsonl` format any harness adapter can emit). */
export type HiveEvent = { type: string } & Record<string, string | number | undefined>

/** Identity of a helper from its delegation input; `agent` is the harness agent or an inferred role. */
export function helperIdentity(input: Record<string, unknown>): Omit<Helper, "parentSessionID"> {
  const text = `${String(input.description ?? "")}\n${String(input.prompt ?? "")}`
  const promise = parsePromise(text)
  const rows = promise?.valid ? [...promise.rows].join(",") : ""
  return { agent: String(input.agent ?? "").toLowerCase(), role: briefRole(text), slice: sliceKey(text) ?? "", rows: reviewScope(text).join(","), ...(rows ? { promise: rows } : {}) }
}

/** Turns a finished reviewer or qa helper's result text into a `review-result` event; other helpers return null. */
export function reviewEvent(sessionID: string, helperID: string, helper: Omit<Helper, "parentSessionID">, text: string): HiveEvent | null {
  const role = helper.agent.includes("reviewer") ? "reviewer" : helper.agent.includes("qa") ? "qa" : ""
  if (!role) return null
  const scope = helper.rows ? helper.rows.split(",") : []
  const code = role === "reviewer" ? reviewOutcome(text, scope) : null
  const discovery = discoveryOutcome(text, helper.promise ? helper.promise.split(",") : [], role)
  if (!code && !discovery.length) return null
  return { type: "review-result", sessionID, helper: helperID, slice: helper.slice, approved: code?.approved.join(",") ?? "", revised: code?.revised ? 1 : 0,
    ...(discovery.length ? { discovery: discovery.join(",") } : {}) }
}

/** Applies one neutral event to memory; used both live and when restoring `events.jsonl`. */
export function apply(state: Memory, event: HiveEvent): void {
  const sessionID = String(event.sessionID ?? "")
  if (!sessionID) return
  if (event.type === "blocked" && event.rule) {
    const ref = `${sessionID}:${event.rule}`
    state.blocks.set(ref, Math.max(state.blocks.get(ref) ?? 0, Number(event.count) || 0))
  }
  if (event.type === "skill-loaded" && event.id === "subagent-delegation") state.skills.add(sessionID)
  if (event.type === "helper-created" && event.parentSessionID)
    state.helpers.set(sessionID, { parentSessionID: String(event.parentSessionID), agent: String(event.agent ?? ""),
      role: String(event.role ?? ""), slice: String(event.slice ?? ""), rows: String(event.rows ?? ""), ...(event.promise ? { promise: String(event.promise) } : {}) })
  // The agent a helper really runs as (a harness pin), which outranks the role its brief names.
  if (event.type === "helper-agent" && event.agent) {
    const known = state.helpers.get(sessionID)
    const parentSessionID = known?.parentSessionID ?? String(event.parentSessionID ?? "")
    if (parentSessionID) state.helpers.set(sessionID, { role: "", slice: "", rows: "", ...known, parentSessionID, agent: String(event.agent).toLowerCase() })
  }
  if (event.type === "helper-finished") state.finished.add(sessionID)
  if (event.type === "review-result") {
    const helper = String(event.helper ?? "")
    if (helper && state.reviewed.has(helper)) return // the same helper result read twice is one review
    if (helper) state.reviewed.add(helper)
    for (const id of String(event.approved ?? "").split(",").filter(Boolean)) state.approvals.add(iscId(id))
    for (const id of String(event.discovery ?? "").split(",").filter(Boolean)) state.approvals.add(`discovery:${iscId(id)}`)
    if (Number(event.revised) && event.slice) {
      const ref = `${sessionID}:${event.slice}`
      state.revisions.set(ref, (state.revisions.get(ref) ?? 0) + 1)
    }
  }
}

export function blockDecision(state: Memory, sessionID: string, rule: string): { block: boolean; count: number; warn: boolean } {
  const key = `${sessionID}:${rule}`
  const count = state.blocks.get(key) ?? 0
  if (count >= 3) return { block: false, count, warn: count === 3 }
  state.blocks.set(key, count + 1)
  return { block: true, count: count + 1, warn: false }
}

export function activeRun(root: string): boolean {
  const card = readFile(resolve(root, ".hivecall/run.md"))
  return /(?:^|\n)\s*(?:[-*]\s*)?\*?status\*?\s*:\s*`?(running|waiting-owner|waiting-usage)\b/i.test(card)
}

function readFile(path: string): string {
  try { return readFileSync(path, "utf8") } catch { return "" }
}

function card(root: string) {
  const text = readFile(resolve(root, ".hivecall/run.md"))
  const status = text.match(/^\s*(?:[-*]\s*)?\*?status\*?\s*:\s*`?([a-z-]+)/im)?.[1]?.toLowerCase() ?? ""
  const goal = text.match(/^\s*goal\s*:\s*(.*?)\s*$/im)?.[1] ?? "(not recorded)"
  const ledger = text.match(/^\s*ledger\s*:\s*(.*?)\s*$/im)?.[1]
  const rules = section(text, "owner rules")
  return { text, status, goal, ledger, rules }
}

function section(text: string, title: string): string[] {
  const lines = text.split(/\r?\n/)
  const start = lines.findIndex((line) => new RegExp(`^##\\s+${title}\\s*$`, "i").test(line))
  if (start < 0) return []
  const end = lines.findIndex((line, index) => index > start && /^##\s+/.test(line))
  return lines.slice(start + 1, end < 0 ? undefined : end).map((line) => line.trim()).filter(Boolean)
}

function ledgerPath(root: string, runCard: ReturnType<typeof card>): string {
  const value = runCard.ledger?.replace(/[`"']/g, "").trim()
  if (value) return isAbsolute(value) ? value : resolve(root, value)
  for (const candidate of [".hivecall/checklist.html", "_ai/docs/ISA.html"]) {
    if (existsSync(resolve(root, candidate))) return resolve(root, candidate)
  }
  return resolve(root, ".hivecall/checklist.html")
}

function shellTargets(command: string): string[] {
  const targets: string[] = []
  for (const pattern of [
    /(?<![\d&<>])>>?\s*["']?([^\s;|&'")]+)/g,
    /\btee\s+(?:-a\s+)?["']?([^\s;|&'"]+)/g,
    /Path\(\s*["']([^"']+)["']\s*\)\.write_(?:text|bytes)/g,
    /open\(\s*["']([^"']+)["']\s*,\s*["'][wa]/g,
  ]) for (const match of command.matchAll(pattern)) targets.push(match[1])
  for (const segment of command.split(/[;\n|]|&&/)) {
    const match = segment.match(/\b(?:sed|perl)\s+-i\S*\s+(.*)/)
    if (match) targets.push(...match[1].split(/\s+/).slice(1).map((token) => token.replace(/["']/g, "")))
  }
  return targets
}

function writesPath(command: string, expected: string, root: string): boolean {
  const full = isAbsolute(expected) ? expected : resolve(root, expected)
  if (shellTargets(command).some((target) => (isAbsolute(target) ? target : resolve(root, target)) === full)) return true
  const quoted = [...command.matchAll(/["']([^"'\n]+)["']/g)].some((match) => {
    const path = match[1]
    return (isAbsolute(path) ? path : resolve(root, path)) === full
  })
  return quoted && /\.write(?:_text)?\s*\(|open\(\s*\w+\s*,\s*["'][wa]/i.test(command)
}

function openItems(ledger: string): string[] {
  const items: string[] = []
  for (const match of ledger.matchAll(/<li\b[^>]*id=["'](ISC-\d+(?:\.\d+)?)["'][^>]*>([\s\S]*?)<\/li>/gi)) {
    if (!/\bchecked\b/i.test(match[2]) && !/parked|owner.only/i.test(match[2])) items.push(match[1].toUpperCase())
  }
  for (const line of ledger.split(/\r?\n/)) {
    const id = line.match(/\bISC-\d+(?:\.\d+)?\b/i)?.[0]
    if (!id) continue
    if (/^\s*[-*]\s+\[ \]/.test(line) && !/parked|owner.only/i.test(line)) items.push(id)
    else if (/^\s*\|/.test(line) && /\b(?:FAIL|BLOCKED)\b/i.test(line) && !/parked|owner.only/i.test(line)) items.push(id)
  }
  return [...new Set(items)]
}

/** The active run's ledger file. */
export function activeLedger(root: string): string {
  return ledgerPath(root, card(root))
}

/** Every item the ledger shows as ticked: a checked box or a PASS row. */
export function tickedItems(text: string): string[] {
  return [...new Set([...checkedItems(text), ...passedItems(text)])]
}

/**
 * Ticked items that have not earned their tick: no exact-id reviewer approval from this run, or no receipt (commit id and
 * existing evidence file) in the ledger as it stands. Items already ticked when the run was first judged are exempt.
 * Judged on the file's end state, whatever tool wrote it; the ledger is never changed.
 */
export function unearned(ledger: string, approvals: Set<string>, grandfathered: Set<string>, root: string): string[] {
  const headings = [...ledger.matchAll(/<h[2-6]\b[^>]*>\s*([^<]*?)\s*<\/h[2-6]\s*>|^\s*#{1,6}\s+(.+?)\s*#*\s*$/gim)]
  const discovery = new Set<string>()
  for (let i = 0; i < headings.length; i++) {
    if ((headings[i][1] ?? headings[i][2]).trim().toLowerCase() === "discovery")
      for (const id of tickedItems(ledger.slice(headings[i].index! + headings[i][0].length, headings[i + 1]?.index ?? ledger.length))) discovery.add(id)
  }
  return tickedItems(ledger).filter((id) => !grandfathered.has(id) && !((approvals.has(id) || (discovery.has(id) && approvals.has(`discovery:${id}`))) && hasReceipt(ledger, id, root)))
}

function checkedItems(text: string): string[] {
  const ids = [...text.matchAll(/<li\b[^>]*id=["'](ISC-\d+(?:\.\d+)*)["'][^>]*>([\s\S]*?)<\/li>/gi)]
    .filter((m) => /\bchecked\b/i.test(m[2])).map((m) => iscId(m[1]))
  // Every item a checked markdown row names, except ids inside a receipt path (`verification/isc-1.log`, `ISC-2.log`, `isc-3-proof.txt`).
  for (const row of text.matchAll(/^\s*[-*]\s+\[x\]\s+(.*)$/gim))
    ids.push(...[...row[1].matchAll(/(?<![/.-])\bISC-\d+(?:\.\d+)*\b(?![._-][a-z])/gi)].map((m) => iscId(m[0])))
  return ids
}

function passedItems(text: string): string[] {
  return [...text.matchAll(/^\s*\|?\s*(ISC-\d+(?:\.\d+)*)\s*\|?\s*PASS\b/gim)].map((m) => iscId(m[1]))
}

/**
 * A receipt for `id` is a commit id and an existing evidence file that follow an exact `id` mention, before the next
 * ISC id on the same line. Per item, not per line, so one line can carry several items' own receipts.
 * A backtick-quoted path must exist exactly; an unquoted one may end in prose punctuation such as `.` or `)`.
 */
function hasReceipt(text: string, id: string, root: string): boolean {
  return text.split(/\r?\n|\\n/).some((line) => {
    // An id inside a path (`verification/isc-1.log`) is part of that receipt, not the start of another item.
    const marks = [...line.matchAll(/(?<![/.-])\bISC-\d+(?:\.\d+)*\b(?![._-][a-z])/gi)]
    return marks.some((mark, i) => {
      if (iscId(mark[0]) !== id) return false
      const segment = line.slice(mark.index!, marks[i + 1]?.index ?? line.length)
      if (!/\bcommit\s+[0-9a-f]{7,40}\b/i.test(segment)) return false
      return [...segment.matchAll(/\bevidence\s*[:=]?\s*(?:`([^`\n]+)`|([^\s`;,|'"<>]+))/gi)].some(([, quoted, bare]) =>
        (quoted ? [quoted] : [bare, bare.replace(/[)\]}.:]+$/, "")]).some((path) => path && existsSync(isAbsolute(path) ? path : resolve(root, path))))
    })
  })
}

function patchFile(patch: string, expected: string, root: string): string {
  const files = [...patch.matchAll(/^\*\*\* (?:Update|Add) File: (.+)$/gm)]
  for (let i = 0; i < files.length; i++) {
    const path = files[i][1]
    if ((isAbsolute(path) ? path : resolve(root, path)) !== expected) continue
    return patch.slice(files[i].index! + files[i][0].length, files[i + 1]?.index ?? patch.length)
  }
  return ""
}

const statusLine = /^\s*(?:[-*]\s*)?\*?status\*?\s*:\s*`?([a-z-]+)/im

/** The run card's status after the write: the card's own status line, never a mention in prose. */
function nextStatus(tool: string, text: string, original: string): string {
  if (tool === "shell") {
    // A command is not the card, so any `status: closed` it names counts as a close (`s.replace('status: running', 'status: closed')`);
    // otherwise the last status it names, else the card's current one. Conservative: prose naming closed is gated too.
    const named = [...text.matchAll(/status\*?\s*:\s*`?([a-z-]+)/gi)].map((m) => m[1].toLowerCase())
    return named.includes("closed") ? "closed" : named.at(-1) ?? statusLine.exec(original)?.[1]?.toLowerCase() ?? ""
  }
  return statusLine.exec(text)?.[1]?.toLowerCase() ?? ""
}

function reportWrite(tool: string, input: Record<string, unknown>, root: string): { text: string; added: boolean; status: string } | null {
  const result = reportText(tool, input, root)
  return result && { ...result, status: nextStatus(tool, result.text, readFile(resolve(root, ".hivecall/run.md"))) }
}

function reportText(tool: string, input: Record<string, unknown>, root: string): { text: string; added: boolean } | null {
  let text = "", path = "", added = false
  if (tool === "write" || tool === "edit") {
    path = String(input.path ?? "")
    const full = isAbsolute(path) ? path : resolve(root, path)
    if (full !== resolve(root, ".hivecall/run.md")) return null
    if (tool === "write") {
      text = String(input.content ?? "")
      added = /##\s+Final report\b/i.test(text)
    } else {
      const original = readFile(full)
      const old = String(input.oldString ?? ""), next = String(input.newString ?? "")
      text = original && original.includes(old) ? original.replace(old, next) : next
      added = !/##\s+Final report\b/i.test(original) && /##\s+Final report\b/i.test(text)
    }
    return { text, added }
  }
  if (tool === "patch") {
    const patch = String(input.patchText ?? "")
    const full = resolve(root, ".hivecall/run.md")
    const block = patchFile(patch, full, root)
    if (!block) return null
    const original = readFile(full)
    const additions = block.split(/\r?\n/).filter((line) => line.startsWith("+") && !line.startsWith("+++"))
      .map((line) => line.slice(1)).join("\n")
    added = !/##\s+Final report\b/i.test(original) && /##\s+Final report\b/i.test(additions)
    return { text: `${additions}\n${original}`, added }
  }
  if (tool === "shell") {
    const command = String(input.command ?? "")
    const target = writesPath(command, ".hivecall/run.md", root)
    if (!target) return null
    const original = readFile(resolve(root, ".hivecall/run.md"))
    added = !/##\s+Final report\b/i.test(original) && /##\s+Final report\b/i.test(command)
    return { text: command, added }
  }
  return null
}

export type Call = { tool: string; input: Record<string, unknown>; sessionID: string; action?: "spawn" | "tell" }

export function ruleFor(call: Call, state: Memory, root: string): { id: string; message: string; detail?: string } | null {
  if (call.tool === "subagent") {
    const input = call.input
    const prompt = String(input.prompt ?? "")
    const target = typeof input.sessionID === "string" ? input.sessionID : ""
    if (target && state.finished.has(target))
      return { id: "no-resume", message: "A finished helper cannot be resumed; start a fresh helper with a Delta." }
    // An own-helper correction keeps its existing brief; unknown targets and new assignments still need one.
    const followup = call.action === "tell" && state.helpers.get(target)?.parentSessionID === call.sessionID
    if (!followup) {
      if (!state.skills.has(call.sessionID)) return { id: "skill-gate", message: "Load `subagent-delegation` before spawning a helper." }
      if (!/talk[- ]?back/i.test(prompt) || !parsePromise(prompt)?.valid)
        return { id: "brief-check", message: "Include the TALK-BACK block and a valid PROMISE line before spawning a helper." }
    }
    const key = sliceKey(`${String(input.description ?? "")}\n${prompt}`)
    const agent = String(input.agent ?? "").toLowerCase()
    const implementationFix = agent === "build" || (agent === "general" && /\b(?:implement|fix|repair|change)\b/i.test(`${String(input.description ?? "")}\n${prompt}`))
    if (implementationFix && key && (state.revisions.get(`${call.sessionID}:${key}`) ?? 0) >= 2)
      return { id: "third-fix", message: "Two REVISE_CODE results on this slice mean split it or change angle; do not send a third fix brief." }
  }

  const proposedCard = reportWrite(call.tool, call.input, root)
  if (proposedCard) {
    const run = card(root)
    const closing = run.status !== "closed" && proposedCard.status === "closed"
    if ((proposedCard.added || closing) && proposedCard.status !== "parked") {
      const path = ledgerPath(root, run)
      const ledger = readFile(path)
      const open = openItems(ledger), bad = unearned(ledger, state.approvals, state.grandfathered, root)
      if (!existsSync(path) || open.length || bad.length) {
        const detail = [open.length ? `open: ${open.join(", ")}` : "", bad.length ? `ticked without approval and receipt: ${bad.join(", ")}` : "",
          existsSync(path) ? "" : "ledger missing"].filter(Boolean).join("; ")
        return { id: "no-early-done", message: "Do not close the run or write the final report while counted ledger items are open or ticked without approval and receipt.", detail }
      }
    }
  }
  return null
}

export function anchor(root: string): string {
  const run = card(root)
  const path = ledgerPath(root, run)
  const items = readFile(path)
  return ["Hivecall run re-anchor:", `Goal: ${run.goal}`, `Open counted items: ${existsSync(path) ? openItems(items).join(", ") || "none" : "(ledger missing)"}`,
    `Owner rules (verbatim):\n${run.rules.join("\n") || "(none recorded)"}`].join("\n")
}
