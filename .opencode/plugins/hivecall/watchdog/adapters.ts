import { Database } from "bun:sqlite"
import { existsSync, readFileSync, statSync } from "node:fs"
import { homedir } from "node:os"
import { basename, isAbsolute, resolve } from "node:path"
import { briefRole, helperIdentity, reviewEvent, type HiveEvent, type Memory } from "./policy"

export type ShellDelegation = {
  call?: { tool: "subagent"; input: Record<string, unknown>; action: "spawn" | "tell" }
  kind?: "spawn" | "tell"
  /** The `--project` a parsed spawn names, to match a project agent pin sent just before it. */
  project?: string
  warning?: string
}

/** BB mirrors a native helper under a thread id; bind it only to an own helper the plugin already saw launch. */
export function bbHelperSession(state: Memory, parent: string, thread: string, path = resolve(homedir(), ".bb/bb.db")): string | null {
  if (!/^thr_[A-Za-z0-9]+$/.test(thread) || !existsSync(path)) return null
  let db: Database | undefined
  try {
    db = new Database(path, { readonly: true })
    const rows = db.query(`SELECT DISTINCT c.provider_thread_id AS session, t.status
      FROM events c JOIN threads t ON t.id = c.thread_id
      JOIN events p ON p.thread_id = t.parent_thread_id
      WHERE t.id = ? AND p.provider_thread_id = ? AND c.provider_thread_id LIKE 'ses_%'`).all(thread, parent) as Array<{ session: string; status: string }>
    const own = rows.filter((row) => state.helpers.get(row.session)?.parentSessionID === parent)
    return own.length === 1 && (own[0].status === "active" || state.finished.has(own[0].session)) ? own[0].session : null
  } catch { return null } // Unavailable mapping gets the normal full-brief checks, not a blanket tell exemption.
  finally { db?.close() }
}

/** Splits a simple command into words; `dynamic[i]` marks words with an unquoted or double-quoted shell expansion. */
function shellWords(text: string): { words: string[]; dynamic: boolean[] } | null {
  const words: string[] = [], dynamic: boolean[] = []
  let word = "", quote = "", escaped = false, started = false, expands = false
  for (const [index, char] of [...text].entries()) {
    if (escaped) {
      word += quote === '"' && !/["\\$`\n]/.test(char) ? `\\${char}` : char
      escaped = false
      started = true
      continue
    }
    if (quote === "'") {
      if (char === "'") quote = ""
      else word += char
      started = true
      continue
    }
    if (char === "`" || char === "$" && /[\w{(@*#?!$-]/.test(text[index + 1] ?? "")) expands = true
    if (quote === '"') {
      if (char === '"') quote = ""
      else if (char === "\\") escaped = true
      else word += char
      started = true
      continue
    }
    if (char === "\\") { escaped = true; started = true; continue }
    if (char === "'" || char === '"') { quote = char; started = true; continue }
    if (/[;&|<>]/.test(char)) return null
    if (/\s/.test(char)) {
      if (started) { words.push(word); dynamic.push(expands) }
      word = ""
      started = false
      expands = false
    } else { word += char; started = true }
  }
  if (escaped || quote) return null
  if (started) { words.push(word); dynamic.push(expands) }
  return { words, dynamic }
}

function option(words: string[], name: string): { value?: string; index: number } | null {
  const index = words.findIndex((word) => word === name || word.startsWith(`${name}=`))
  if (index < 0) return null
  const value = words[index].startsWith(`${name}=`) ? words[index].slice(name.length + 1) : words[index + 1]
  return value === undefined ? { index } : { value, index: words[index].startsWith(`${name}=`) ? index : index + 1 }
}

type Doc = { body: string; dynamic: boolean }

/** A regular file of at most 256 KB, else null: a FIFO, device or huge file must not hang or flood the hook. */
function readSmallFile(path: string): string | null {
  try {
    const stat = statSync(path)
    return stat.isFile() && stat.size <= 256 * 1024 ? readFileSync(path, "utf8") : null
  } catch { return null }
}

/**
 * Pulls heredoc bodies out of a command: each `<<DELIM` becomes `\0<n>\0`, and an inline `"$(cat <<DELIM …)"`
 * becomes `\x01<n>\x01`, so the remaining text splits into simple words.
 */
function heredocs(command: string): { text: string; docs: Doc[] } {
  const docs: Doc[] = []
  const pattern = /<<(?!<)-?[ \t]*(['"]?)([A-Za-z_][\w.-]*)\1([^\n]*)\n([\s\S]*?)^[\t ]*\2[\t ]*(?:\n|$)/m
  let text = command
  for (let match = pattern.exec(text); match; match = pattern.exec(text)) {
    // An unquoted delimiter lets the shell expand the body.
    docs.push({ body: match[4].replace(/^\t/gm, ""), dynamic: !match[1] && /\$[\w{(]|`/.test(match[4]) })
    text = `${text.slice(0, match.index)}\0${docs.length - 1}\0${match[3]}\n${text.slice(match.index + match[0].length)}`
  }
  text = text.replace(/"\$\(\s*cat\s+\0(\d+)\0\s*\)"|\$\(\s*cat\s+\0(\d+)\0\s*\)/g, (_, quoted, bare) => `\x01${quoted ?? bare}\x01`)
  return { text, docs }
}

/** Per character: true when it sits outside quotes and is not escaped. */
function unquoted(text: string): boolean[] {
  const mask: boolean[] = []
  let quote = "", escaped = false
  for (const char of text) {
    const outside = !quote && !escaped && char !== "\\" && char !== "'" && char !== '"'
    if (escaped) escaped = false
    else if (quote === "'") { if (char === "'") quote = "" }
    else if (char === "\\") escaped = true
    else if (quote === '"') { if (char === '"') quote = "" }
    else if (char === "'" || char === '"') quote = char
    for (let i = 0; i < char.length; i++) mask.push(outside)
  }
  return mask
}

/** Role of a BB helper named in its brief; BB spawn has no agent flag, so an unnamed BB thread counts as general. */
export function inferredAgent(text: string): string {
  return briefRole(text) || "general"
}

const tellValueOptions = new Set(["--message-file", "--model", "--service-tier", "--reasoning-level", "--permission-mode", "--mode", "--send-at", "--file", "--image"])
const dynamicWarning = "BB delegation text is built by the shell at run time; left ungated."
const bbDelegation = /(^|[\s;&|(`])((?:[^\s;&|()'"`]+\/)?bb\s+thread\s+(spawn|tell))\b/g

type BriefContext = { words: string[]; docs: Doc[]; writes: Array<[string, Doc]>; before: string; outside: string; cwd: string }

/**
 * Text of a `--prompt-file`/`--message-file` brief: a stdin heredoc, the one heredoc the same command writes to that
 * path before the spawn (and nothing else touches it there), or the file now.
 */
function briefFile(value: string | undefined, isDynamic: boolean, ctx: BriefContext): { text?: string; warning?: string } {
  if (value === undefined || value === "") return { warning: "BB brief file option has no path; left ungated." }
  if (isDynamic) return { warning: dynamicWarning }
  const stdin = ctx.words.map((word) => /^\0(\d+)\0$/.exec(word)?.[1]).find((n) => n !== undefined)
  if (value === "-" || value === "/dev/stdin") {
    const doc = stdin === undefined ? undefined : ctx.docs[Number(stdin)]
    if (!doc) return { warning: "BB brief comes from stdin the hook cannot see; left ungated." }
    return doc.dynamic ? { warning: dynamicWarning } : { text: doc.body }
  }
  if (!isAbsolute(value) && /(?:^|[\s;&|(])cd\s/.test(ctx.before)) return { warning: "BB brief file path is relative to a changed directory; left ungated." }
  const target = resolve(ctx.cwd, value)
  const writes = ctx.writes.filter(([path]) => path === target)
  // One heredoc write, and the file name appears nowhere else before the spawn (no second write, append or move).
  if (writes.length === 1 && ctx.before.split(basename(target)).length === 2)
    return writes[0][1].dynamic ? { warning: dynamicWarning } : { text: writes[0][1].body }
  if (writes.length || ctx.outside.includes(value)) return { warning: "BB brief file is changed by the same command; left ungated." }
  const text = readSmallFile(resolve(ctx.cwd, value))
  return text === null ? { warning: "BB brief file is missing, not a regular file, or over 256 KB; left ungated." } : { text }
}

/**
 * Maps one `bb thread spawn|tell` in a shell command to the neutral `subagent` policy input. The brief may be inline,
 * an inline heredoc, or a `--prompt-file`/`--message-file` (stdin heredoc, a heredoc written earlier in the same
 * command, or the file as it is at hook time). Anything the hook cannot see exactly fails open with a warning.
 */
export function shellDelegation(command: string, cwd = process.cwd()): ShellDelegation {
  const { text, docs } = heredocs(command)
  const mask = unquoted(text)
  const found = [...text.matchAll(bbDelegation)].filter((match) => mask[match.index! + match[1].length])
  if (found.length !== 1) return /\bbb\s+thread\s+(?:spawn|tell)\b/.test(text)
    ? { warning: found.length ? "Several BB delegations in one command; left ungated." : "BB delegation command is embedded or wrapped; left ungated." }
    : {}

  const start = found[0].index! + found[0][1].length, kind = found[0][3] as "spawn" | "tell"
  let end = start
  while (end < text.length && !(mask[end] && /[;&|()<>\n]/.test(text[end]))) end++
  const parsed = shellWords(text.slice(start, end))
  if (!parsed) return { kind, warning: "BB delegation command could not be parsed; left ungated." }
  const { words, dynamic } = parsed
  words.forEach((word, i) => {
    words[i] = word.replace(/\x01(\d+)\x01/g, (_, n) => { dynamic[i] ||= docs[Number(n)].dynamic; return docs[Number(n)].body })
  })
  const before = text.slice(0, start)
  const writes = [...before.matchAll(/\bcat\s*>\s*(['"]?)([^\s'"<>;&|]+)\1\s*\0(\d+)\0|\bcat\s*\0(\d+)\0\s*>\s*(['"]?)([^\s'"<>;&|]+)\5/g)]
    .map((match): [string, Doc] => [resolve(cwd, match[2] ?? match[6]), docs[Number(match[3] ?? match[4])]])
  const ctx = { words, docs, writes, before, outside: before + text.slice(end), cwd }
  const file = (name: string) => {
    const found = option(words, name)
    return found ? briefFile(found.value, found.value !== undefined && dynamic[found.index], ctx) : null
  }
  const input: Record<string, unknown> = { agent: "", description: "", prompt: "" }

  if (kind === "spawn") {
    const fromFile = file("--prompt-file")
    if (fromFile?.warning) return { kind, warning: fromFile.warning }
    const promptOption = option(words, "--prompt")
    const prompt = fromFile?.text ?? promptOption?.value
    if (prompt === undefined) return { kind, warning: "BB spawn has no parseable --prompt; left ungated." }
    const title = option(words, "--title")
    if (!fromFile && dynamic[promptOption!.index] || title?.value !== undefined && dynamic[title.index]) return { kind, warning: dynamicWarning }
    input.prompt = prompt
    input.description = title?.value ?? ""
    input.agent = option(words, "--agent")?.value ?? inferredAgent(`${input.description}\n${prompt}`)
    const project = option(words, "--project")
    if (project?.value && !dynamic[project.index]) return { call: { tool: "subagent", input, action: kind }, kind, project: project.value }
  } else {
    const fromFile = file("--message-file")
    if (fromFile?.warning) return { kind, warning: fromFile.warning }
    const positional: number[] = []
    for (let i = 3; i < words.length; i++) {
      if (tellValueOptions.has(words[i])) i++
      else if (!words[i].startsWith("--") && !words[i].startsWith("\0")) positional.push(i)
    }
    const [targetAt, ...messageAt] = positional
    if (targetAt === undefined || dynamic[targetAt]) return { kind, warning: "BB tell target could not be parsed; left ungated." }
    if (!fromFile && messageAt.some((i) => dynamic[i])) return { kind, warning: dynamicWarning }
    const message = fromFile?.text ?? messageAt.map((i) => words[i]).join(" ")
    if (!message) return { kind, warning: "BB tell message could not be parsed; left ungated." }
    // Worker reports to the parent are not new delegation briefs.
    if (/^\s*(?:BUG|BLOCKED|QUESTION|STOP|RESULT|PASS|FAIL|ANSWER)\b/i.test(message)) return {}
    input.prompt = message
    input.description = "BB thread tell"
    input.agent = inferredAgent(message)
    input.sessionID = words[targetAt] // the helper being resumed, for the neutral no-resume rule
  }

  return { call: { tool: "subagent", input, action: kind }, kind }
}

/** An agent pin sent through the OpenCode BB plugin: a BB thread, or the project's next new thread. */
export type BbStamp = { thread?: string; project?: string; agent: string }

const unverifiedPin = { warning: "BB agent pin is not one plain executed stampAgent call; not counted as a verified pin." }

/** JSON a pipe producer writes: `printf '%s' '<json>'`, `printf '<json>'`, `echo [-n] '<json>'`, or `cat` of a heredoc. */
function producedText(words: string[], docs: Doc[]): string | null {
  const [name, ...args] = words
  const doc = (word: string) => { const found = docs[Number(/^\0(\d+)\0$/.exec(word)?.[1] ?? NaN)]; return found && !found.dynamic ? found.body : null }
  if (name === "printf") return args.length === 2 && args[0] === "%s" ? args[1] : args.length === 1 && !/[%\\]/.test(args[0]) ? args[0] : null
  if (name === "echo") { const rest = args[0] === "-n" ? args.slice(1) : args; return rest.some((arg) => arg.startsWith("-")) ? null : rest.join(" ") }
  return name === "cat" && args.length === 1 ? doc(args[0]) : null
}

/**
 * The pin one executed `bb plugin rpc call --input-file /dev/stdin opencode stampAgent` sends. The command must be
 * that call alone, fed by a stdin heredoc or one `printf`/`echo`/`cat` pipe; stamp text inside quotes, comments,
 * heredoc bodies, echo/printf arguments or chained commands is never a pin.
 */
export function bbAgentStamp(command: string): { stamp?: BbStamp; warning?: string } {
  if (!/\bstampAgent\b/.test(command)) return {}
  const { text, docs } = heredocs(command)
  const body = text.trim(), mask = unquoted(body), parts: string[] = []
  let from = 0
  for (let i = 0; i < body.length; i++) {
    if (!mask[i] || !/[\n|]/.test(body[i])) continue
    if (body[i] === "\n" || body[i + 1] === "|") return unverifiedPin
    parts.push(body.slice(from, i))
    from = i + 1
  }
  parts.push(body.slice(from))
  const commands = parts.map(shellWords)
  if (parts.length > 2 || commands.some((parsed) => !parsed || parsed.dynamic.some(Boolean))) return unverifiedPin
  const words = commands.at(-1)!.words
  const stdin: string[] = [], rest: string[] = []
  let file: string | undefined, files = 0
  for (let i = 4; i < words.length; i++) {
    if (words[i] === "--input-file") { file = words[++i]; files++ }
    else if (words[i].startsWith("--input-file=")) { file = words[i].slice(13); files++ }
    else if (/^\0\d+\0$/.test(words[i])) stdin.push(words[i])
    else if (words[i] !== "--json") rest.push(words[i])
  }
  if (words.slice(0, 4).join(" ") !== "bb plugin rpc call" || rest.join(" ") !== "opencode stampAgent" || files !== 1 || (file !== "/dev/stdin" && file !== "-"))
    return unverifiedPin
  // The payload reaches stdin from exactly one place: the pipe producer, or a heredoc on the call itself.
  const payload = parts.length === 2 ? (stdin.length ? null : producedText(commands[0]!.words, docs))
    : stdin.length === 1 ? producedText(["cat", stdin[0]], docs) : null
  if (payload === null) return unverifiedPin
  let pin: Record<string, unknown>
  try { pin = JSON.parse(payload) } catch { return unverifiedPin }
  const value = (key: string) => pin && typeof pin === "object" && typeof pin[key] === "string" ? String(pin[key]).trim() : ""
  const agent = value("agent").toLowerCase(), thread = value("threadId"), project = value("projectId")
  if (!/^[\w.-]+$/.test(agent)) return unverifiedPin
  if (thread) return /^thr_[A-Za-z0-9]+$/.test(thread) ? { stamp: { thread, agent } } : unverifiedPin
  return project ? { stamp: { project, agent } } : unverifiedPin
}

/** True when a stampAgent RPC's output is its success result, `{ "ok": true }`. */
export function stampSucceeded(output: string): boolean {
  const objects = output.match(/\{[^{}]*\}/g) ?? []
  try { return objects.length === 1 && JSON.stringify(JSON.parse(objects[0])) === '{"ok":true}' } catch { return false }
}

/**
 * A verified thread pin: the RPC succeeded and it pins a helper this session saw spawn to the role its brief named.
 * Anything else returns null; that helper then simply cannot approve ticks.
 */
export function bbPinEvent(state: Memory, sessionID: string, stamp: BbStamp, output: string): HiveEvent | null {
  const helper = stamp.thread ? state.helpers.get(stamp.thread) : undefined
  if (!helper || helper.parentSessionID !== sessionID || helper.role !== stamp.agent || !stampSucceeded(output)) return null
  return { type: "helper-agent", sessionID: stamp.thread!, parentSessionID: sessionID, agent: stamp.agent }
}

// BB child-thread lifecycle, mapped to the neutral helper events the policy consumes.
const threadID = "thr_[A-Za-z0-9]+"
type Identity = ReturnType<typeof helperIdentity>

/** `bb thread spawn` output (`Thread spawned: thr_…`, the `--json` object, or a bare id piped out of it) names the new helper.
 * Its agent stays unverified (empty) until a `stampAgent` pin is seen: brief text can name a role but cannot prove it. */
export function bbSpawnEvent(sessionID: string, identity: Identity, output: string): HiveEvent | null {
  const thread = output.match(new RegExp(`Thread spawned:\\s*(${threadID})`))?.[1] ??
    output.match(new RegExp(`"id"\\s*:\\s*"(${threadID})"`))?.[1] ?? output.trim().match(new RegExp(`^(${threadID})$`))?.[1]
  return thread ? { type: "helper-created", sessionID: thread, parentSessionID: sessionID, ...identity, agent: "" } : null
}

/** A plain `bb thread output <id> [--json]` read; its tool output is that helper's final result. */
export function bbOutputRead(command: string): { thread: string; json: boolean } | null {
  const match = new RegExp(`^\\s*(?:[^\\s;&|]+/)?bb\\s+thread\\s+output\\s+(?:--json\\s+)?(${threadID})(\\s+--json)?\\s*$`).exec(command)
  return match ? { thread: match[1], json: /--json/.test(match[0]) } : null
}

export function bbReadEvent(state: Memory, read: { thread: string; json: boolean }, output: string): HiveEvent | null {
  const helper = state.helpers.get(read.thread)
  if (!helper) return null
  let text = output
  if (read.json) try { text = String(JSON.parse(output).output ?? "") } catch { text = "" }
  return reviewEvent(helper.parentSessionID, read.thread, helper, text)
}

/**
 * BB lifecycle notices reach the parent session as a prompt: `[bb system]`, then `@thread:thr_… completed:` and the
 * child's final output, or a `Child thread updates:` list. Only `completed` marks a helper finished.
 */
export function bbNoticeEvents(state: Memory, sessionID: string, text: string): HiveEvent[] {
  if (!/^\s*"?\[bb system\]/.test(text)) return [] // `opencode run` was seen wrapping prompt text in quotes
  const marks = [...text.matchAll(new RegExp(`@thread:(${threadID}) (completed|failed|was interrupted)\\b([^\\n]*)`, "g"))]
  return marks.flatMap((mark, i) => {
    const thread = mark[1], helper = state.helpers.get(thread)
    const body = mark[3].trimStart().startsWith(":") ? text.slice(mark.index! + mark[0].length, marks[i + 1]?.index ?? text.length) : ""
    const events: Array<HiveEvent | null> = [
      mark[2] === "completed" ? { type: "helper-finished", sessionID: thread, parentSessionID: helper?.parentSessionID ?? sessionID } : null,
      helper && body.trim() ? reviewEvent(helper.parentSessionID, thread, helper, body) : null,
    ]
    return events.filter((event): event is HiveEvent => event !== null)
  })
}
