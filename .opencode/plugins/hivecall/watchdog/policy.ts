import { spawnSync } from "node:child_process"
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { basename, isAbsolute, relative, resolve } from "node:path"
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

/** Items a qa result fails: those its negative lines name, or every item when a negative line names none. */
function qaFailed(text: string, items: string[]): string[] {
  const negative = text.split(/\r?\n/).filter((line) => /\b(?:FAIL|BLOCKED|NOT_REPRODUCED)\b/.test(line))
  if (negative.some((line) => !iscIds(line).length)) return items
  const named = new Set(negative.flatMap(iscIds))
  return items.filter((id) => named.has(id))
}

/** `role` "pass" is a qa result read for PASS alone (REPRODUCED is a repro, not a verified pass). */
function discoveryOutcome(text: string, scope: string[], role: string): string[] {
  const qa = role === "qa" || role === "pass"
  const approve = role === "pass" ? /\bPASS\b/ : qa ? /\b(?:REPRODUCED|PASS)\b/ : /\b(?:APPROVE_PLAN|SELECTED)\b/
  const revise = qa ? /\b(?:NOT_REPRODUCED|BLOCKED|FAIL)\b/ : /\b(?:REVISE_PLAN|ASK_USER)\b/
  const verdict = (line: string): Verdict | null => {
    const yes = approve.test(line), no = revise.test(line)
    return yes === no ? null : yes ? "approve" : "revise"
  }
  const lines = text.split(/\r?\n/)
  // A negative on a line naming no ISC id vetoes every scoped id, even after an approving Decision/Result line.
  if (lines.some((line) => !iscIds(line).length && revise.test(line))) return []
  const token = role === "pass" ? "PASS|NOT_REPRODUCED|BLOCKED|FAIL" : qa ? "REPRODUCED|PASS|NOT_REPRODUCED|BLOCKED|FAIL" : "APPROVE_PLAN|SELECTED|REVISE_PLAN|ASK_USER"
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

export type Helper = { parentSessionID: string; agent: string; role: string; slice: string; rows: string; promise?: string; commits?: string }

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
  /** Failed verdicts (REVISE_CODE, FAIL, BLOCKED, NOT_REPRODUCED) per item: attempts that did not raise the score. */
  failures: Map<string, number>
  /** Failed verdicts since the last earned tick, run-wide (hill climb). */
  sinceTick: number
  /** Accepted RE-PLANs per item (`run` for the run-wide one): its failure count at the time, and its Next. */
  replans: Map<string, { at: number; next: string }>
}

export function memory(): Memory {
  return { blocks: new Map(), skills: new Set(), finished: new Set(), approvals: new Set(), grandfathered: new Set(), revisions: new Map(),
    helpers: new Map(), reviewed: new Set(), failures: new Map(), sinceTick: 0, replans: new Map() }
}

/** Items a helper works on: its PROMISE rows and the rows its brief names. */
function helperItems(helper: Pick<Helper, "rows" | "promise">): string[] {
  return [...new Set([...(helper.promise ?? "").split(","), ...helper.rows.split(",")].filter(Boolean))]
}



/** Neutral event rows (the `events.jsonl` format any harness adapter can emit). */
export type HiveEvent = { type: string } & Record<string, string | number | undefined>

/** Identity of a helper from its delegation input; `agent` is the harness agent or an inferred role. */
export function helperIdentity(input: Record<string, unknown>): Omit<Helper, "parentSessionID"> {
  const text = `${String(input.description ?? "")}\n${String(input.prompt ?? "")}`
  const promise = parsePromise(text)
  const rows = promise?.valid ? [...promise.rows].join(",") : ""
  // Commit ids the brief names: a qa PASS is about those candidates only.
  const commits = [...new Set(text.match(/\b[0-9a-f]{7,40}\b/gi) ?? [])].slice(0, 12).join(",")
  return { agent: String(input.agent ?? "").toLowerCase(), role: briefRole(text), slice: sliceKey(text) ?? "", rows: reviewScope(text).join(","),
    ...(rows ? { promise: rows } : {}), ...(commits ? { commits } : {}) }
}

/** Turns a finished reviewer or qa helper's result text into a `review-result` event; other helpers return null. */
export function reviewEvent(sessionID: string, helperID: string, helper: Omit<Helper, "parentSessionID">, text: string): HiveEvent | null {
  const role = helper.agent.includes("reviewer") ? "reviewer" : helper.agent.includes("qa") ? "qa" : ""
  if (!role) return null
  const scope = helper.rows ? helper.rows.split(",") : []
  const code = role === "reviewer" ? reviewOutcome(text, scope) : null
  const discovery = discoveryOutcome(text, helper.promise ? helper.promise.split(",") : [], role)
  const passed = role === "qa" ? discoveryOutcome(text, helper.promise ? helper.promise.split(",") : [], "pass") : []
  // A failed attempt for the hill-climb count: a REVISE_CODE, or a qa negative, on the items the helper worked on.
  const failed = role === "qa" ? qaFailed(text, helperItems(helper)) : code?.revised ? helperItems(helper).filter((id) => !code.approved.includes(id)) : []
  if (!code && !discovery.length && !failed.length) return null
  return { type: "review-result", sessionID, helper: helperID, slice: helper.slice, approved: code?.approved.join(",") ?? "", revised: code?.revised ? 1 : 0,
    ...(discovery.length ? { discovery: discovery.join(",") } : {}), ...(passed.length && helper.commits ? { passed: passed.join(","), commits: helper.commits } : {}),
    ...(failed.length ? { failed: failed.join(",") } : {}) }
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
      role: String(event.role ?? ""), slice: String(event.slice ?? ""), rows: String(event.rows ?? ""), ...(event.promise ? { promise: String(event.promise) } : {}),
      ...(event.commits ? { commits: String(event.commits) } : {}) })
  // The agent a helper really runs as (a harness pin), which outranks the role its brief names.
  if (event.type === "helper-agent" && event.agent) {
    const known = state.helpers.get(sessionID)
    const parentSessionID = known?.parentSessionID ?? String(event.parentSessionID ?? "")
    if (parentSessionID) state.helpers.set(sessionID, { role: "", slice: "", rows: "", ...known, parentSessionID, agent: String(event.agent).toLowerCase() })
  }
  if (event.type === "helper-finished") state.finished.add(sessionID)
  if (event.type === "allowed" && event.action === "tick") state.sinceTick = 0
  if (event.type === "replan" && event.item) {
    const item = String(event.item)
    if (item === "run") state.sinceTick = 0
    state.replans.set(item, { at: item === "run" ? 0 : state.failures.get(item) ?? 0, next: String(event.next ?? "") })
  }
  if (event.type === "review-result") {
    const helper = String(event.helper ?? "")
    if (helper && state.reviewed.has(helper)) return // the same helper result read twice is one review
    if (helper) state.reviewed.add(helper)
    for (const id of String(event.approved ?? "").split(",").filter(Boolean)) state.approvals.add(iscId(id))
    const failed = String(event.failed ?? "").split(",").filter(Boolean)
    for (const id of failed) state.failures.set(iscId(id), (state.failures.get(iscId(id)) ?? 0) + 1)
    // A later failure on an item supersedes its earlier qa PASSes.
    for (const id of failed) for (const pass of [...state.approvals]) if (pass.startsWith(`pass:${iscId(id)}@`)) state.approvals.delete(pass)
    if (failed.length) state.sinceTick++
    for (const id of String(event.discovery ?? "").split(",").filter(Boolean)) state.approvals.add(`discovery:${iscId(id)}`)
    for (const id of String(event.passed ?? "").split(",").filter(Boolean))
      for (const sha of String(event.commits ?? "").split(",").filter(Boolean)) state.approvals.add(`pass:${iscId(id)}@${sha.toLowerCase()}`)
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

/** Copies a closed run's record (events, run card, ledger) to `<home>/.hivecall/runs/<repo>/<run>/` so archiving the
 *  worktree keeps it for the retro. Returns the folder, or null when there is no run card. */
export function archiveRun(root: string, home: string): string | null {
  const runCard = resolve(root, ".hivecall/run.md")
  const text = readFile(runCard)
  if (!text) return null
  const owner = text.match(/^\s*orchestrator\s*:.*$/im)?.[0] ?? text
  const run = owner.match(/\b(thr_[a-z0-9]+)/i)?.[1] ?? owner.match(/\b(ses_[A-Za-z0-9]+)/)?.[1] ?? "run"
  const started = text.match(/^\s*started\s*:\s*(\d{4}-\d{2}-\d{2})/im)?.[1] ?? "undated"
  const dir = resolve(home, ".hivecall/runs", basename(root), `${started}-${run}`)
  mkdirSync(dir, { recursive: true })
  const ledger = activeLedger(root)
  for (const [from, name] of [[resolve(root, ".hivecall/events.jsonl"), "events.jsonl"], [runCard, "run.md"], [ledger, basename(ledger)]])
    if (existsSync(from)) copyFileSync(from, resolve(dir, name))
  writeFileSync(resolve(dir, "source.txt"), `${root}\n`)
  return dir
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
  const canary = new Set(canaryMissing(ledger, root))
  return tickedItems(ledger).filter((id) => !grandfathered.has(id) && !((approvals.has(id) || (approvals.has(`discovery:${id}`) && discovery.has(id)) ||
    (qaPassed(approvals, id, receiptCommit(ledger, id)) && lowRisk(ledger, root, receiptCommit(ledger, id)))) && hasReceipt(ledger, id, root) && !canary.has(id)))
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
  return receipts(text, id).some((segment) => {
    if (!/\bcommit\s+[0-9a-f]{7,40}\b/i.test(segment)) return false
    return [...segment.matchAll(/\bevidence\s*[:=]?\s*(?:`([^`\n]+)`|([^\s`;,|'"<>]+))/gi)].some(([, quoted, bare]) =>
      (quoted ? [quoted] : [bare, bare.replace(/[)\]}.:]+$/, "")]).some((path) => path && existsSync(isAbsolute(path) ? path : resolve(root, path))))
  })
}

/** Every ledger segment about `id`: from an exact `id` mention to the next ISC id on the same line, in file order. */
function receipts(text: string, id: string): string[] {
  const segments: string[] = []
  for (const line of text.split(/\r?\n|\\n/)) {
    // An id inside a path (`verification/isc-1.log`) is part of that receipt, not the start of another item.
    const marks = [...line.matchAll(/(?<![/.-])\bISC-\d+(?:\.\d+)*\b(?![._-][a-z])/gi)]
    marks.forEach((mark, i) => { if (iscId(mark[0]) === id) segments.push(line.slice(mark.index!, marks[i + 1]?.index ?? line.length)) })
  }
  return segments
}

/** The commit the item's latest receipt names (the last line per id wins), or "". */
function receiptCommit(text: string, id: string): string {
  return receipts(text, id).map((segment) => /\bcommit\s+([0-9a-f]{7,40})\b/i.exec(segment)?.[1] ?? "").filter(Boolean).at(-1) ?? ""
}

/** Read-only git in the run's checkout; null when git or the repo is unavailable (gates never alarm on missing data). */
function git(root: string, args: string[]): string | null {
  try {
    const result = spawnSync("git", args, { cwd: root, encoding: "utf8", timeout: 5000 })
    return result.status === 0 ? result.stdout : null
  } catch { return null }
}

const commitFiles = new Map<string, string[] | null>()
/** `name-status` rows a commit changed against its first parent (renames detected only when exact); cached, commits never change. */
function changedBy(root: string, commit: string): string[] | null {
  const cacheKey = `${root}\n${commit}`
  if (!commitFiles.has(cacheKey)) {
    const out = git(root, ["diff", "--name-status", "-M100%", `${commit}^1`, commit])
    commitFiles.set(cacheKey, out === null ? null : out.split("\n").filter(Boolean))
  }
  return commitFiles.get(cacheKey)!
}

/** The item's own text in the ledger: its `<li id>` body, else the first checkbox line naming it. */
function itemText(ledger: string, id: string): string {
  for (const match of ledger.matchAll(/<li\b[^>]*id=["'](ISC-\d+(?:\.\d+)*)["'][^>]*>([\s\S]*?)<\/li>/gi)) if (iscId(match[1]) === id) return match[2]
  return ledger.split(/\r?\n/).find((line) => /^\s*[-*]\s+\[[ x]\]/i.test(line) && iscIds(line).includes(id)) ?? ""
}

/**
 * A ticked item whose receipt commit edits a file its own `check:` names needs a `CANARY:` line in its receipt: proof that a
 * known-broken case still fails, so a check is never bent until it passes.
 */
export function canaryMissing(ledger: string, root: string): string[] {
  return tickedItems(ledger).filter((id) => {
    const commit = receiptCommit(ledger, id)
    const check = /\bcheck\s*:\s*([\s\S]*)/i.exec(itemText(ledger, id).replace(/<[^>]+>/g, " "))?.[1] ?? ""
    const named = [...check.matchAll(/[\w@.-]*(?:\/[\w@.-]+)+|[\w@-]+\.[a-z]{1,6}\b/gi)].map((m) => m[0].replace(/^\.?\//, ""))
    if (!commit || !named.length) return false
    const files = (changedBy(root, commit) ?? []).map((row) => row.split("\t").at(-1)!)
    const touched = files.some((file) => named.some((name) => file === name || file.endsWith(`/${name}`) || name.endsWith(`/${file}`)))
    // The canary must sit on a receipt for this commit; an older canary proves an older version of the check.
    return touched && !receipts(ledger, id).some((segment) => segment.includes(commit) && /\bCANARY\s*:/i.test(segment))
  })
}

/** A qa PASS on `id` whose brief named this exact commit (either id may be the short form). */
function qaPassed(approvals: Set<string>, id: string, commit: string): boolean {
  const sha = commit.toLowerCase()
  return Boolean(sha) && [...approvals].some((key) => key.startsWith(`pass:${id}@`) &&
    ((tested) => tested.startsWith(sha) || sha.startsWith(tested))(key.slice(`pass:${id}@`.length)))
}

const lowRiskPath = /(?:^|\/)(?:tests?|__tests__|spec|specs|docs?)\/|\.(?:test|spec)\.\w+$|Tests?\.\w+$|\.(?:md|mdx|rst)$/i
/**
 * Proof sized to risk: a commit that only renames/moves files exactly, or changes tests or docs (Markdown/reST; never `.txt`, which is often config), on top of a commit already
 * proven (the run base or checkpoint, or another ticked item's receipt commit) needs no code review; its qa PASS ticks it.
 */
function lowRisk(ledger: string, root: string, commit: string): boolean {
  const rows = changedBy(root, commit)
  if (!rows?.length || !rows.every((row) => /^R100\t/.test(row) || lowRiskPath.test(row.split("\t").at(-1)!))) return false
  const parent = git(root, ["rev-parse", "--verify", "--quiet", `${commit}^1`])?.trim()
  const checkpoints = [...(card(root).text.match(/^\s*(?:base|checkpoint)\s*:.*$/gim)?.join("\n") ?? "").matchAll(/\b([0-9a-f]{7,40})\b/gi)].map((m) => m[1])
  // A FAIL row's commit is not proven: only ticked items' receipt commits count.
  const proven = [...checkpoints, ...tickedItems(ledger).map((id) => receiptCommit(ledger, id))]
    .filter((sha) => sha && !commit.startsWith(sha) && !sha.startsWith(commit))
  return Boolean(parent && proven.some((sha) => parent.startsWith(sha)))
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
/** `key` scopes the block-then-allow count (for example one item), so one paused item never spends another's pauses. */
/** `hold` keeps blocking after the 3-pause cap, because one line the caller can write clears it. */
export type Violation = { id: string; message: string; detail?: string; key?: string; hold?: boolean }

/** Ids the run card lists on `Not counted:` lines. */
export function notCounted(text: string): Set<string> {
  return new Set([...text.matchAll(/^.*\bnot counted\s*:(.*)$/gim)].flatMap((m) => iscIds(m[1])))
}

const HILL_CLIMB_ITEM = 3, HILL_CLIMB_RUN = 5
type Replan = { item: string; next: string; problem: string }

/**
 * `RE-PLAN item=<id|run>` blocks in a brief: `Tried:` what the last attempts did, `Evidence:` an existing file, and `Next:` a
 * new angle, a split or park that differs from the item's previous Next. `problem` names what is missing; "" when valid.
 */
function replansIn(prompt: string, state: Memory, root: string): Replan[] {
  return prompt.split(/^(?=\s*RE-?PLAN\b)/im).filter((block) => /^\s*RE-?PLAN\b/i.test(block)).map((block) => {
    const raw = /^\s*RE-?PLAN\b[^\n]*?\bitem\s*=\s*([\w.-]+)/i.exec(block)?.[1] ?? ""
    const item = /^run$/i.test(raw) ? "run" : /^ISC-/i.test(raw) ? iscId(raw) : raw
    const field = (name: string) => new RegExp(`^\\s*${name}\\s*:\\s*(.+)$`, "im").exec(block)?.[1].trim() ?? ""
    const tried = field("Tried"), evidence = field("Evidence").replace(/[`"']/g, "").split(/\s+/)[0], next = field("Next")
    const normalized = next.toLowerCase().replace(/\s+/g, " ")
    const problem = !item ? "no item=" : !tried ? "no Tried:" : !evidence || !existsSync(isAbsolute(evidence) ? evidence : resolve(root, evidence))
      ? `Evidence: ${evidence || "(none)"} is not an existing file` : !/^(?:new angle|split|park)\b/i.test(next) ? "Next: must start with new angle, split or park"
      : state.replans.get(item)?.next === normalized ? "Next: repeats the previous RE-PLAN word for word" : ""
    return { item, next: normalized, problem }
  })
}

/** Valid RE-PLAN blocks of an allowed brief, as `replan` events; recording one resets that item's hill-climb count. */
export function replanEvents(input: Record<string, unknown>, state: Memory, root: string): HiveEvent[] {
  return replansIn(String(input.prompt ?? ""), state, root).filter((plan) => !plan.problem).map((plan) => ({ type: "replan", item: plan.item, next: plan.next }))
}

const reason = (prompt: string) => /^\s*WHY\s*:\s*\S/im.test(prompt)

/** The commit-like tokens a brief names that resolve to commits here; null when this is not a git checkout. */
function namedCommits(root: string, prompt: string): string[] | null {
  if (git(root, ["rev-parse", "--git-dir"]) === null) return null
  return [...new Set(prompt.match(/\b[0-9a-f]{7,40}\b/g) ?? [])].slice(0, 12)
    .filter((sha) => git(root, ["rev-parse", "--verify", "--quiet", `${sha}^{commit}`]) !== null)
}

/** Files with uncommitted edits in the run's checkout, other than the run's own `.hivecall/` and ledger. */
export function dirtyFiles(root: string): string[] {
  const ledger = activeLedger(root)
  return (git(root, ["status", "--porcelain", "--untracked-files=no"]) ?? "").split("\n").map((line) => line.slice(3).trim()).filter(Boolean)
    .filter((path) => !path.startsWith(".hivecall/") && resolve(root, path) !== ledger)
}

/**
 * Progress gates on a new helper brief (HOW-TO-WORK.md, Hill climb and Reflect, then adapt). Each pauses the spawn once per
 * key and clears with one line in the brief: a RE-PLAN block, or `WHY:`.
 */
function progressGate(input: Record<string, unknown>, prompt: string, state: Memory, root: string): Violation | null {
  const identity = helperIdentity(input)
  const items = helperItems(identity)
  const role = identity.agent.includes("reviewer") || identity.role === "reviewer" ? "reviewer"
    : identity.agent.includes("qa") || identity.role === "qa" ? "qa" : identity.agent || identity.role
  const ledger = readFile(activeLedger(root))
  const ticked = new Set(tickedItems(ledger))
  const plans = new Map(replansIn(prompt, state, root).map((plan) => [plan.item, plan]))
  const needs = (item: string, count: number): Violation | null => {
    const plan = plans.get(item)
    if (plan && !plan.problem) return null
    return { id: "replan", key: `replan:${item}`, message: "", detail: `${count} failed attempts on ${item === "run" ? "the run" : item} with no new tick` +
      (plan ? `; RE-PLAN item=${item}: ${plan.problem}` : `; add RE-PLAN item=${item}`) }
  }
  for (const item of items) {
    if (ticked.has(item)) continue
    const count = (state.failures.get(item) ?? 0) - (state.replans.get(item)?.at ?? 0)
    if (count >= HILL_CLIMB_ITEM) { const gate = needs(item, count); if (gate) return gate }
  }
  if (state.sinceTick >= HILL_CLIMB_RUN) { const gate = needs("run", state.sinceTick); if (gate) return gate }

  if ((role === "reviewer" || role === "qa") && items.length && items.every((item) => ticked.has(item)) && !reason(prompt)) {
    const unchanged = items.every((item) => {
      const commit = receiptCommit(ledger, item)
      // The ledger and run files change with every tick; they are not the item's inputs.
      const ledgerFile = relative(root, ledgerPath(root, card(root)))
      const changed = commit ? git(root, ["diff", "--name-only", commit, "--", ".", ":(exclude).hivecall",
        ...(ledgerFile && !ledgerFile.startsWith("..") ? [`:(exclude)${ledgerFile}`] : [])]) : null
      return changed !== null && !changed.trim()
    })
    if (unchanged) return { id: "no-redo", key: `no-redo:${items.join(",")}`, message: "", detail: `${items.join(", ")} already passed and nothing changed since their receipt commits` }
  }
  if (role === "qa" && !reason(prompt)) {
    const commits = namedCommits(root, prompt)
    if (commits && !commits.length) return { id: "qa-commit", key: "qa-commit", message: "", detail: "the brief names no commit that exists in this checkout" }
  }
  return null
}

export function ruleFor(call: Call, state: Memory, root: string): Violation | null {
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
    // Right agent for the job: a brief that names a qa or reviewer role runs as that agent.
    const role = briefRole(`${String(input.description ?? "")}\n${prompt}`)
    if (!followup && agent && (role === "qa" || role === "reviewer") && agentMismatch(role, agent))
      return { id: "right-agent", message: `This brief is ${role} work; spawn it with agent=${role}.`, detail: `agent=${agent}` }
    if (!followup) {
      const gate = progressGate(input, prompt, state, root)
      if (gate) return gate
    }
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
        // A checked box the plugin did not count stays visible as such (invariant 1): after the usual three pauses the close
        // still waits until the run card names every such id on a `Not counted:` line.
        const listed = notCounted(`${run.text}\n${proposedCard.text}`)
        const unlisted = bad.filter((id) => !listed.has(id))
        const detail = [open.length ? `open: ${open.join(", ")}` : "", bad.length ? `ticked without approval and receipt: ${bad.join(", ")}` : "",
          existsSync(path) ? "" : "ledger missing",
          unlisted.length ? `to close with them still ticked, the run card must say \`Not counted: ${unlisted.join(", ")}\`` : ""].filter(Boolean).join("; ")
        return { id: "no-early-done", message: "Do not close the run or write the final report while counted ledger items are open or ticked without approval and receipt.", detail,
          ...(unlisted.length ? { hold: true } : {}) }
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
