import { iscId, iscIds } from "./promise"

/**
 * Text edits behind the `hivecall_ledger` and `hivecall_card` tools: the orchestrator decides the content, these only type
 * it in, in the one format the ledger template and the gates read (references/checklist-template.html, kickoff.md).
 * Every edit returns the new text or a loud error; nothing is written on a miss.
 */
export type LedgerEdit = {
  action: "tick" | "fail" | "park" | "add"
  id: string
  observed?: string; evidence?: string; commit?: string; verifier?: string; canary?: string
  reason?: string; unlock?: string
  text?: string; feature?: string
}
export type CardEdit = { action: "status" | "note"; status?: string; section?: string; text?: string }
type Result = { text: string } | { error: string }

const escape = (value: string) => value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\s*(?:\n|\\n)\s*/g, " ").trim() // the receipt reader also splits on a literal \n
const path = (value: string) => /\s/.test(value) ? `\`${value}\`` : value

/** The `<li id>` opening tag of an item and its checkbox input, by canonical id. */
function item(html: string, id: string) {
  for (const match of html.matchAll(/<li\b[^>]*\bid=["'](ISC-[\d.]+)["'][^>]*>/gi)) {
    if (iscId(match[1]) !== id) continue
    const start = match.index! + match[0].length
    const input = /^\s*<input\b[^>]*>/i.exec(html.slice(start))
    return { label: match[1], input: input && /type=["']?checkbox/i.test(input[0]) ? { at: start, tag: input[0] } : null }
  }
  return null
}

function setInput(html: string, at: number, tag: string, change: (tag: string) => string): string {
  return html.slice(0, at) + change(tag) + html.slice(at + tag.length)
}
const unchecked = (tag: string) => tag.replace(/\s+checked(?:=["'][^"']*["'])?/gi, "")
const checked = (tag: string) => /\schecked\b/i.test(tag) ? tag : tag.replace(/\s*\/?>$/, (end) => ` checked${end.trim() === "/>" ? " />" : ">"}`)
const parked = (tag: string) => /data-status=/i.test(tag) ? tag.replace(/data-status=["'][^"']*["']/i, 'data-status="parked"')
  : tag.replace(/\s*\/?>$/, (end) => ` data-status="parked"${end.trim() === "/>" ? " />" : ">"}`)

/** Appends one result line under `#verification`. */
function appendVerification(html: string, line: string): Result {
  const section = html.search(/<section\b[^>]*\bid=["']verification["']/i)
  const end = section < 0 ? -1 : html.indexOf("</ul>", section)
  if (end < 0) return { error: "the ledger has no <section id=\"verification\"> list to append results to" }
  return { text: `${html.slice(0, end)}<li>${line}</li>\n${html.slice(end)}` }
}

/** Keeps the stored `progress` row equal to the ticked boxes. */
function progress(html: string): string {
  const boxes = [...html.matchAll(/<li\b[^>]*\bid=["']ISC-[\d.]+["'][^>]*>\s*(<input\b[^>]*>)/gi)].filter((m) => /type=["']?checkbox/i.test(m[1]))
  const done = boxes.filter((m) => /\schecked\b/i.test(m[1])).length
  return html.replace(/(<th>\s*progress\s*<\/th>\s*<td>)[^<]*(<\/td>)/i, `$1${done}/${boxes.length}$2`)
}

export function editLedger(html: string, edit: LedgerEdit): Result {
  if (!/<li\b[^>]*\bid=["']ISC-/i.test(html) && edit.action !== "add") return { error: "hivecall_ledger edits the HTML checklist only; this ledger has no <li id=\"ISC-…\"> items" }
  if (!/^(?:ISC-)?\d+(?:\.\d+)*$/i.test(edit.id ?? "")) return { error: `id must look like ISC-12, got "${edit.id}"` }
  const id = iscId(edit.id)
  const free = [edit.observed, edit.reason, edit.unlock, edit.canary, edit.text].filter(Boolean).join(" ")
  const others = iscIds(free).filter((other) => other !== id)
  if (others.length) return { error: `free text names ${others.join(", ")}; another item's id would split ${id}'s receipt line, so describe it without the id` }
  const found = item(html, id)
  if (edit.action === "add") {
    if (found) return { error: `${id} already exists; the tool never rewrites an item's text` }
    if (!edit.text?.trim()) return { error: "add needs text: the observable behavior and its check" }
    const label = `ISC-${Number(id.slice(4).split(".")[0])}${id.includes(".") ? id.slice(id.indexOf(".")) : ""}`
    const criteria = html.search(/<section\b[^>]*\bid=["']criteria["']/i)
    if (criteria < 0) return { error: "the ledger has no <section id=\"criteria\">" }
    const close = html.indexOf("</section>", criteria)
    const heading = edit.feature ? html.slice(criteria, close).search(new RegExp(`<h3>\\s*${edit.feature.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*</h3>`, "i")) : -1
    if (edit.feature && heading < 0) return { error: `no <h3>${edit.feature}</h3> in the checklist; pass an existing feature or none` }
    const list = heading >= 0 ? html.indexOf("</ul>", criteria + heading) : html.lastIndexOf("</ul>", close)
    if (list < 0 || list > close) return { error: "no checklist <ul> to add the item to" }
    return { text: progress(`${html.slice(0, list)}  <li id="${label}"><input type="checkbox" disabled> ${label}: ${escape(edit.text)}</li>\n${html.slice(list)}`) }
  }
  if (!found) return { error: `${id} is not on the ledger` }
  if (!found.input) return { error: `${found.label} has no checkbox right after its <li id>` }
  const { at, tag } = found.input
  const need = (fields: Array<keyof LedgerEdit>) => fields.filter((field) => !String(edit[field] ?? "").trim())
  if (edit.action === "tick") {
    const missing = need(["observed", "evidence", "commit", "verifier"])
    if (missing.length) return { error: `tick needs ${missing.join(", ")}` }
    if (!/^[0-9a-f]{7,40}$/i.test(edit.commit!)) return { error: `commit must be a 7-40 character hex id, got "${edit.commit}"` }
    const line = `${found.label}: PASS - ${escape(edit.observed!)}; evidence ${path(edit.evidence!)}; verifier ${escape(edit.verifier!)}; commit ${edit.commit}` +
      (edit.canary ? `; CANARY: ${escape(edit.canary)}` : "")
    const appended = appendVerification(setInput(html, at, tag, (t) => checked(unchecked(t).replace(/\sdata-status=["']parked["']/i, ""))), line)
    return "error" in appended ? appended : { text: progress(appended.text) }
  }
  if (edit.action === "fail") {
    const missing = need(["reason"])
    if (missing.length) return { error: "fail needs reason" }
    const line = `${found.label}: FAIL - ${escape(edit.reason!)}` + (edit.evidence ? `; evidence ${path(edit.evidence)}` : "") +
      (edit.verifier ? `; verifier ${escape(edit.verifier)}` : "") + (edit.commit ? `; commit ${edit.commit}` : "")
    const appended = appendVerification(setInput(html, at, tag, unchecked), line)
    return "error" in appended ? appended : { text: progress(appended.text) }
  }
  if (edit.action === "park") {
    const missing = need(["reason", "unlock"])
    if (missing.length) return { error: `park needs ${missing.join(", ")}` }
    const line = `${found.label}: BLOCKED - parked; reason: ${escape(edit.reason!)}; unlock: ${escape(edit.unlock!)}` + (edit.evidence ? `; evidence ${path(edit.evidence)}` : "")
    const appended = appendVerification(setInput(html, at, tag, (t) => parked(unchecked(t))), line)
    return "error" in appended ? appended : { text: progress(appended.text) }
  }
  return { error: `unknown action "${edit.action}"; use tick, fail, park or add` }
}

const statuses = ["running", "waiting-owner", "waiting-usage", "closed"]

export function editCard(card: string, edit: CardEdit): Result {
  if (edit.action === "status") {
    if (!statuses.includes(edit.status ?? "")) return { error: `status must be one of ${statuses.join(", ")}` }
    const line = /^(\s*(?:[-*]\s*)?\*?status\*?\s*:\s*`?)[a-z-]+/im
    if (!line.test(card)) return { error: "the run card has no status: line" }
    return { text: card.replace(line, `$1${edit.status}`) }
  }
  if (edit.action === "note") {
    const section = edit.section?.trim(), text = edit.text?.trim()
    if (!section || !text) return { error: "note needs section and text" }
    const lines = card.split("\n")
    const start = lines.findIndex((line) => line.trim().toLowerCase() === `## ${section.toLowerCase()}`)
    if (start < 0) return { text: `${card.replace(/\s*$/, "")}\n\n## ${section}\n${text}\n` }
    let end = lines.findIndex((line, index) => index > start && /^##\s+/.test(line))
    if (end < 0) end = lines.length
    while (end > start + 1 && !lines[end - 1].trim()) end--
    lines.splice(end, 0, text)
    return { text: lines.join("\n") }
  }
  return { error: `unknown action "${edit.action}"; use status or note` }
}
