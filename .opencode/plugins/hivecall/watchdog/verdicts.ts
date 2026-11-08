import { iscId } from "./promise"
import { helperItems, type Helper, type HiveEvent } from "./policy"

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
export function verdictProblems(helper: Pick<Helper, "agent" | "rows" | "promise">, verdicts: Verdict[]): string[] {
  const role = helperRole(helper.agent)
  if (!role) return ["only a verified reviewer or qa helper of this run records verdicts"]
  const allowed: readonly string[] = VERDICTS[role]
  const scope = new Set(helperItems(helper).map(iscId))
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

/** The exact `VERDICT ISC-n TOKEN` lines in a BB helper's result; a later line for an id replaces an earlier one. */
export function verdictLines(text: string): Verdict[] {
  const byId = new Map<string, string>()
  for (const m of text.matchAll(/^[ \t]*VERDICT[ \t]+(ISC-\d+(?:\.\d+)*)[ \t]+([A-Z_]+)[ \t]*$/gm)) byId.set(iscId(m[1]), m[2])
  return [...byId].map(([id, verdict]) => ({ id, verdict }))
}

/** The `review-result` event for recorded verdicts (already checked with `verdictProblems`). */
export function verdictEvent(sessionID: string, key: string, helper: Pick<Helper, "slice" | "commits">, verdicts: Verdict[]): HiveEvent {
  const ids = (...tokens: string[]) => verdicts.filter((v) => tokens.includes(v.verdict)).map((v) => iscId(v.id))
  const list = (values: string[]) => values.length ? values.join(",") : undefined
  const passed = ids("PASS")
  return { type: "review-result", sessionID, helper: key, slice: helper.slice, approved: ids("APPROVE_CODE").join(","),
    revised: ids("REVISE_CODE").length ? 1 : 0, withheld: list(ids("REVISE_CODE")), undiscovered: list(ids("REVISE_PLAN", "ASK_USER")),
    discovery: list(ids("APPROVE_PLAN", "SELECTED", "REPRODUCED", "PASS")),
    ...(passed.length && helper.commits ? { passed: passed.join(","), commits: helper.commits } : {}),
    failed: list(ids("REVISE_CODE", "FAIL", "BLOCKED", "NOT_REPRODUCED")) }
}
