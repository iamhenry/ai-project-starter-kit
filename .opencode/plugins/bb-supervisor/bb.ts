import { Database } from "bun:sqlite"
import { existsSync } from "node:fs"
import { homedir } from "node:os"
import { resolve } from "node:path"
import { log } from "./gate"

/** BB state the plugin reads (read-only database) and the one message it sends. */

/** Gate status by Mission session, shared with the root's re-anchor (same server process). */
export const gateStatus = new Map<string, string>()
/** BB calls, swappable in tests: the Mission's thread and parent, and a message to the parent. */
export const bb = {
  db: resolve(homedir(), ".bb/bb.db"), // BB's database, read-only
  mission(sessionID: string, db = bb.db): { id: string; parent: string } | null {
    if (!existsSync(db)) return null
    let conn: Database | undefined
    try {
      conn = new Database(db, { readonly: true })
      return conn.query(`SELECT t.id, t.parent_thread_id AS parent FROM events e JOIN threads t ON t.id = e.thread_id
        WHERE e.provider_thread_id = ? AND t.parent_thread_id IS NOT NULL LIMIT 1`).get(sessionID) as { id: string; parent: string } | null
    } catch (error) { log("BB thread lookup", error); return null }
    finally { conn?.close() }
  },
  tell(thread: string, message: string): boolean {
    return Bun.spawnSync([process.env.BB_CLI || "bb", "thread", "tell", thread, message]).exitCode === 0
  },
}

/** Root thread, its active direct Missions, and the Task key in each Mission title (`🚀 KEY-1 outcome`). */
export function anchorText(sessionID: string, db = bb.db, status = (session: string) => gateStatus.get(session)): string {
  if (!existsSync(db)) return ""
  let conn: Database | undefined
  try {
    conn = new Database(db, { readonly: true })
    const self = conn.query(`SELECT t.id, t.title, t.project_id AS project, t.environment_id AS env FROM events e JOIN threads t ON t.id = e.thread_id
      WHERE e.provider_thread_id = ? LIMIT 1`).get(sessionID) as { id: string; title: string; project: string; env: string } | null
    if (!self) return ""
    const missions = conn.query(`SELECT id, title, status FROM threads WHERE parent_thread_id = ? AND archived_at IS NULL AND deleted_at IS NULL
      ORDER BY created_at`).all(self.id) as Array<{ id: string; title: string | null; status: string }>
    const sessionOf = conn.query(`SELECT provider_thread_id AS session FROM events WHERE thread_id = ? AND provider_thread_id LIKE 'ses_%' LIMIT 1`)
    const lines = missions.map((m) => {
      const key = /\b([A-Z][A-Z0-9]+-\d+)\b/.exec(m.title ?? "")?.[1]
      const session = (sessionOf.get(m.id) as { session: string } | null)?.session
      const gate = session ? status(session) : undefined
      return `- @thread:${m.id} "${m.title ?? ""}" status=${m.status}${gate ? ` gate: ${gate}` : ""}${key ? `\n::task{key="${key}"}` : ""}`
    })
    return [
      "[bb-supervisor re-anchor] You are the root Supervisor (bb-supervisor). You coordinate only: you never edit outside _ai/task/**, never wait on threads, and Missions run as build or orchestrator, never as you. " +
        "A small Mission's gate status is the done gate's verdict; report a small Mission as done only when its gate says DONE accepted. A large Mission's done comes from its hivecall checklist.",
      `Your thread: ${self.id} "${self.title ?? ""}" project=${self.project} environment=${self.env}.`,
      missions.length ? `Active Missions (BB state, newest last):\n${lines.join("\n")}` : "Active Missions: none.",
    ].join("\n")
  } catch (error) { log("BB state read", error); return "" }
  finally { conn?.close() }
}

