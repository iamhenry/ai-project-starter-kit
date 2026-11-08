import { iscId } from "./promise"
import type { Helper, HiveEvent } from "./policy"

/**
 * Verdicts are structured data, never read from prose (invariant 4). A native reviewer or qa records them with the
 * `hivecall_verdict` tool; a BB helper, which cannot call it, writes one exact line per item: `VERDICT ISC-2 REVISE_CODE`.
 */
export const VERDICTS = {
  reviewer: ["APPROVE_CODE", "REVISE_CODE", "APPROVE_PLAN", "SELECTED", "REVISE_PLAN", "ASK_USER"],
  qa: ["PASS", "FAIL", "BLOCKED", "REPRODUCED", "NOT_REPRODUCED"],
} as const
export type Verdict = { id: string; verdict: string }

export function helperRole(agent: string): "reviewer" | "qa" | "" {
  const name = agent.toLowerCase()
  return name.includes("reviewer") ? "reviewer" : name.includes("qa") ? "qa" : ""
}

/** Why these verdicts cannot be recorded for this helper; empty when they all can. */
export function verdictProblems(helper: Pick<Helper, "agent" | "promise">, verdicts: Verdict[]): string[] {
  const role = helperRole(helper.agent)
  if (!role) return ["only a verified reviewer or qa helper of this run records verdicts"]
  const allowed: readonly string[] = VERDICTS[role]
  // Only a valid PROMISE line assigns items; ids merely mentioned in the brief do not.
  const scope = new Set((helper.promise ?? "").split(",").filter(Boolean).map(iscId))
  const seen = new Set<string>()
  const problems: string[] = []
  if (!verdicts.length) problems.push("no verdicts given")
  for (const { id, verdict } of verdicts) {
    const item = /^ISC-\d+(?:\.\d+)*$/i.test(id) ? iscId(id) : ""
    if (!item) problems.push(`"${id}" is not an item id like ISC-2`)
    else if (!scope.has(item)) problems.push(`${item} is not one of the items your brief assigned (${[...scope].join(", ") || "none"})`)
    else if (seen.has(item)) problems.push(`${item} is given twice`)
    if (!allowed.includes(verdict)) problems.push(`${verdict} is not a ${role} verdict (${allowed.join(", ")})`)
    if (item) seen.add(item)
  }
  return problems
}

/**
 * The exact `VERDICT ISC-n TOKEN` lines that end a BB helper's result (the closing block only, so an example quoted
 * earlier never counts); a later line for an id replaces an earlier one.
 */
export function verdictLines(text: string): Verdict[] {
  const byId = new Map<string, string>()
  const lines = text.trimEnd().split(/\r?\n/)
  const block: RegExpExecArray[] = []
  for (let m; (m = /^[ \t]*VERDICT[ \t]+(ISC-\d+(?:\.\d+)*)[ \t]+([A-Z_]+)[ \t]*$/.exec(lines.at(-1) ?? "")); lines.pop()) block.unshift(m)
  for (const m of block) byId.set(iscId(m[1]), m[2])
  return [...byId].map(([id, verdict]) => ({ id, verdict }))
}

/** The `review-result` event for recorded verdicts (already checked with `verdictProblems`). */
export function verdictEvent(sessionID: string, key: string, helper: Pick<Helper, "slice" | "commits">, verdicts: Verdict[]): HiveEvent {
  const ids = (...tokens: string[]) => verdicts.filter((v) => tokens.includes(v.verdict)).map((v) => iscId(v.id))
  const list = (values: string[]) => values.length ? values.join(",") : undefined
  const passed = ids("PASS")
  // A plan send-back (REVISE_PLAN, ASK_USER) withdraws the item's code and plan approvals; negatives cancel everything
  // through `failed`; a positive verdict never removes another helper's approval.
  return { type: "review-result", sessionID, helper: key, slice: helper.slice, approved: ids("APPROVE_CODE").join(","),
    revised: ids("REVISE_CODE").length ? 1 : 0, reset: list(ids("REVISE_PLAN", "ASK_USER")),
    verdicts: verdicts.map((v) => `${iscId(v.id)}=${v.verdict}`).join(","),
    discovery: list(ids("APPROVE_PLAN", "SELECTED", "REPRODUCED", "PASS")),
    ...(passed.length && helper.commits ? { passed: passed.join(","), commits: helper.commits } : {}),
    failed: list(ids("REVISE_CODE", "FAIL", "BLOCKED", "NOT_REPRODUCED")) }
}
