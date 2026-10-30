import { existsSync, mkdtempSync, copyFileSync, rmSync, statSync } from "node:fs"
import { tmpdir } from "node:os"
import { isAbsolute, join, relative, resolve } from "node:path"
import { briefRole } from "../hivecall/watchdog/policy"

/** Pure done-gate checks: endings, verdicts, receipts and worktree snapshots. No host or BB calls. */

export const SEND_BACK_LIMIT = 3

// approvedAt / passedAt: worktree snapshots the reviewer approved and qa passed. receipts: accepted qa receipt files;
// they were new when their qa started and are left out of every snapshot, so saving them never voids a gate.
// proof: content hashes of the receipts behind the current PASS; if one is deleted or changed, the PASS stops counting.
// approvedTime: when the approval arrived; a qa run counts only if it started after it.
export type Gate = { approvedAt: string | null; approvedTime: number; passedAt: string | null; receipts: string[]; proof: Record<string, string>; sentBack: number; escalated: boolean; lastText: string; qaNote: string; wrongAgent: string }

export const ENDINGS = ["DONE", "BLOCKED", "NEEDS DECISION", "UNVERIFIED"] as const
/** The ending a Mission report declares on its first non-empty line, e.g. `ENDING: NEEDS DECISION`; null if none. */
export function ending(text: string): (typeof ENDINGS)[number] | null {
  const first = text.trim().split(/\r?\n/)[0] ?? ""
  return (/^[\W_]*ENDING[\W_]*:\W*(DONE|BLOCKED|NEEDS DECISION|UNVERIFIED)\b/i.exec(first)?.[1]?.toUpperCase() as (typeof ENDINGS)[number]) ?? null
}

/** The child's own result: the body inside the host's `<subagent …>` envelope, which also echoes the parent's description. */
export function resultBody(text: string, description: string): string | null {
  if (!text.startsWith("<subagent ")) return text
  const header = `description="${description}">\n`
  const at = text.indexOf(header)
  if (at < 0 || text.slice(0, at).includes("\n") || !text.endsWith("\n</subagent>")) return null
  return text.slice(at + header.length, -"\n</subagent>".length)
}

/** Agents allowed for the role a helper brief names; a role with no entry is unchecked. */
const ROLE_AGENTS: Record<string, string[]> = { build: ["build"], reviewer: ["reviewer"], qa: ["qa"], research: ["atlas", "voyager", "plan"] }
/** Why a helper may not run: its brief names a role its agent does not fill. Empty when it may run. */
export function helperRole(input: Record<string, unknown>): string {
  const description = String(input.description ?? ""), text = `${description}\n${String(input.prompt ?? "")}`
  const named = (t: string) => {
    const qa = /\bverification[- ]gate\b/i.test(t), review = /\bcode[- ]quality[- ]gate\b/i.test(t)
    return qa !== review ? (qa ? "qa" : "reviewer") : ""
  }
  // "act as the verification-gate QA", "serve as reviewer": the helper is asked to fill that role.
  const as = /\b(?:act|acting|serve|serving|work|working|run|running)\s+as\s+(?:the\s+|a\s+|an\s+)?`?(qa|tester|verification[- ]gate|reviewer|code[- ]quality[- ]gate|builder|build)\b/i.exec(text)?.[1]?.toLowerCase()
  const asRole = !as ? "" : /qa|tester|verification/.test(as) ? "qa" : /review|quality/.test(as) ? "reviewer" : "build"
  return briefRole(text) || asRole || named(description)
}
export function wrongAgent(input: Record<string, unknown>): string {
  const role = helperRole(input)
  const agent = String(input.agent ?? "").toLowerCase()
  const allowed = ROLE_AGENTS[role]
  return allowed && agent && !allowed.includes(agent)
    ? `[bb-supervisor] This helper's brief is ${role} work, but it would run as \`${agent}\`. Run it as \`${allowed.join("` or `")}\` instead.` : ""
}

export function log(operation: string, error: unknown) {
  try { console.error(`[bb-supervisor] ${operation} failed (${error instanceof Error ? error.message : "unknown error"})`) } catch {}
}

/** Overall reviewer decision: a `Decision:`/`Verdict:` line wins, else the one decision word used. Per-item approvals don't count. */
export function reviewDecision(text: string): "APPROVE_CODE" | "REVISE_CODE" | "ASK_USER" | null {
  const line = /^\W*(?:decision|verdict|result)\b[^:\n]*:\W*(APPROVE_CODE|REVISE_CODE|ASK_USER)\b/im.exec(text)?.[1]
  if (line) return line.toUpperCase() as "ASK_USER"
  const words = new Set([...text.matchAll(/\b(APPROVE_CODE|REVISE_CODE|ASK_USER)\b/g)].map((m) => m[1]))
  return words.size === 1 ? [...words][0] as "ASK_USER" : null
}

/** QA verdict from a verification-gate result: a `Verdict:`/`Result:` line wins, else the one verdict word used. */
export function qaVerdict(text: string): "PASS" | "FAIL" | "BLOCKED" | null {
  const line = /^\W*(?:verdict|result|status)\b[^:\n]*:\W*(PASS|FAIL|BLOCKED)\b/im.exec(text)?.[1]
  if (line) return line.toUpperCase() as "PASS"
  const words = new Set([...text.matchAll(/\b(PASS|FAIL|BLOCKED)\b/g)].map((m) => m[1]))
  return words.size === 1 ? [...words][0] as "PASS" : null
}

/** Files a result names: markdown link targets, backticked paths, and bare absolute paths. */
export function namedFiles(text: string, dir: string): string[] {
  const found = [...text.matchAll(/\]\(([^)\s]+)\)|`([^`\s]+)`|(?:^|[\s(])(\/[^\s)`'"<>]+)/gm)].map((m) => m[1] ?? m[2] ?? m[3])
  return [...new Set(found.map((f) => f.replace(/^file:\/\//, "").replace(/[.,;:]+$/, "")).filter((f) => /[\/.]/.test(f))
    .map((f) => isAbsolute(f) ? f : resolve(dir, f)))]
}

/** Receipts a qa result names: not empty, written after `since` (ms), and new, i.e. not a worktree file at snapshot `at`. */
export function freshReceipts(text: string, dir: string, since: number, at: string): string[] {
  return namedFiles(text, dir).filter((f) => {
    try { const st = statSync(f); if (!st.isFile() || st.size === 0 || st.mtimeMs < since) return false } catch { return false }
    const rel = relative(dir, f)
    return rel.startsWith("..") || isAbsolute(rel) || git(dir, ["cat-file", "-e", `${at}:${rel}`]) === null
  })
}

export const git = (dir: string, args: string[], env?: Record<string, string>) => {
  const out = Bun.spawnSync(["git", "-C", dir, ...args], { env: { ...process.env, ...env } })
  return out.exitCode === 0 ? out.stdout.toString().trim() : null
}

/** What the Mission still needs, judged against the worktree snapshot it has now. */
export function missing(gate: Pick<Gate, "approvedAt" | "passedAt" | "qaNote">, now: string): string[] {
  const stale = (at: string | null) => at !== null && at !== now ? " (files changed after it)" : ""
  return [gate.approvedAt !== now && `a fresh reviewer APPROVE_CODE of the current files${stale(gate.approvedAt)}`,
    gate.passedAt !== now && `a fresh qa PASS after that approval that names its receipt file${stale(gate.passedAt)}${gate.qaNote ? ` (${gate.qaNote})` : ""}`]
    .filter(Boolean) as string[]
}

/** Content hash of the whole worktree, untracked files included (ignored files and accepted `receipts` excluded), via a throwaway index. */
export function snapshot(dir: string, receipts: string[] = []): string {
  const run = (args: string[], env?: Record<string, string>) => {
    const out = git(dir, args, env)
    if (out === null) throw new Error(`git ${args[0]} failed`)
    return out
  }
  const temp = mkdtempSync(join(tmpdir(), "bbsup-"))
  try {
    const index = join(temp, "index"), real = run(["rev-parse", "--git-path", "index"]), env = { GIT_INDEX_FILE: index }
    const source = isAbsolute(real) ? real : resolve(dir, real)
    if (existsSync(source)) copyFileSync(source, index) // reuse cached hashes; only changed files are re-read
    run(["add", "-A"], env)
    const inside = receipts.map((f) => relative(dir, f)).filter((r) => !r.startsWith("..") && !isAbsolute(r))
    if (inside.length) run(["rm", "--cached", "-q", "--ignore-unmatch", "--", ...inside], env)
    return run(["write-tree"], env)
  } catch (error) { log("worktree snapshot", error); return "" }
  finally { rmSync(temp, { recursive: true, force: true }) }
}

