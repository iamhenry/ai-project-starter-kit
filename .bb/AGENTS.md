# AGENTS.md — Global BB Instructions (macvm)

BB injects this file into every provider-backed thread. Use it to orient quickly: where projects live, how to delegate through BB, and which commands map to common actions. `/Users/macvm` is the machine-wide fallback workspace; prefer a dedicated project below.

---

## 1. Where Things Live

| Path | What |
| --- | --- |
| `~/Desktop/Projects/` | **Main projects root.** Subdirs: `mac/`, `mobile/`, `other/`, `web/` |
| `~/src/` | Secondary workspace for BB plugin experiments (`bb-plugin-agent-switcher`, `bb-plugin-files`, `bb-plugin-filetree`, `bb-plugin-session-brief`) |
| `~/SYSTEMS.md` | Host services (BB, OpenChamber, Paseo, T3 Code) — launchd labels, restart/update procedures |
| `~/.bb/AGENTS.md` | This file; BB injects it into every provider-backed thread |
| `~/.bb/` | BB data dir (config, plugins, themes, skills) |

### BB Projects (registered)

| Project ID | Name | Path |
| --- | --- | --- |
| `proj_iekidk5qz8` | sonara-ios-app | `~/Desktop/Projects/mobile/sonara-ios-app` |
| `proj_wkj7q7zn9f` | mac-quotes-app | `~/Desktop/Projects/mac/mac-quotes-app` |
| `proj_dey5ufjf4n` | ai-project-starter-kit | `~/Desktop/Projects/other/ai-project-starter-kit` |
| `proj_ujm8nucspz` | bb-plugin-session-brief | `~/Desktop/Projects/other/bb-plugin-session-brief` |
| `proj_z8a7i24wnt` | bb-plugin-opencode | `~/Desktop/Projects/other/bb-plugin-opencode` |
| `proj_mpw77yyiiy` | bb-plugin-dashboard-sidebar | `~/Desktop/Projects/other/bb-plugin-dashboard-sidebar` |
| `proj_5tf55t8fjj` | bb-plugin-gitx | `~/Desktop/Projects/other/bb-plugin-gitx` |
| `proj_vudqmhwkzq` | macvm (this workspace) | `/Users/macvm` |
| `proj_48qxqrxgwy` | Projects (umbrella workspace) | `~/Desktop/Projects` |

Fetch current truth anytime: `bb project list --json`. New project: `bb project create --name <n> --root <path> --machine <id>` (machine list via `bb machine list`).

---

## 2. BB Core Concepts (30 seconds)

- **Project** = a registered workspace/repo. **Thread** = one agent conversation (the unit of work). **Environment** = where a thread runs (checkout or isolated worktree). **Machine** = execution host (primary host id: `host_mxhri6p392`).
- Threads can be **parent → child**. Parent coordinates and receives lifecycle notifications.
- Delegation defaults to one level: root coordinator → terminal worker. A selected primary agent may define a narrower explicit delegation topology; otherwise direct children do not delegate.
- Thread shells normally expose `BB_PROJECT_ID`, `BB_THREAD_ID`, `BB_ENVIRONMENT_ID`, and `BB_CLI`, but provider shells may occasionally lack them. Missing variables do **not** prove the conversation is outside BB.
- Use `--json` on supported operational and inspection subcommands; check `--help` when unsure. Deep reference: `bb guide <threads|projects|environments|providers|machines|terminals|agent-configuration>`.

---

## 3. Thread Role Router

The selected agent prompt owns any specialized operating roles. These global defaults apply otherwise.

| Signal | Role | Required behavior |
|---|---|---|
| `thread.parentThreadId == null` | **Root coordinator** | Follow the normal task router and delegate only independent, bounded work. |
| `thread.parentThreadId != null` | **Terminal worker** | Complete the bounded assignment and report to the parent; do not delegate unless the selected agent prompt explicitly assigns a bounded exception. |

---

## 4. Delegation via Child Threads

**Default:** only a root coordinator delegates independent, parallelizable work. A direct child is a terminal worker and completes its assignment itself unless the selected agent prompt explicitly assigns a bounded exception.

### Resolve the parent first

Start with:

```bash
bb thread show --self --json
```

If it succeeds:

- `thread.parentThreadId == null` → root coordinator; follow the selected agent prompt and normal task router.
- `thread.parentThreadId != null` → terminal worker unless the selected agent prompt explicitly assigns a bounded exception. Without that exception, do **not** call `bb thread spawn`, OpenCode `Task`, `functions.task`, or any other agent/subagent workflow; report blockers to the parent instead.

If it fails because `BB_THREAD_ID` is unset, distinguish two cases:

1. **This conversation is visibly running in BB or the user asked to use it as the parent.** Recover the current thread ID instead of spawning an unparented thread. Search with a unique, non-sensitive phrase from the latest user message, then verify the candidate's project, environment, status, and log:

   ```bash
   bb thread search "<unique recent phrase>" --json
   bb thread show <candidate-id> --json
   bb thread log <candidate-id> --limit 5
   ```

   Continue only after one candidate is clearly the current conversation. Use its ID with `--parent-thread` and re-check `parentThreadId` to enforce the depth limit.

2. **This is genuinely a plain shell/session with no intended BB parent.** Spawn a root thread only when independent root work is intentional.

Never treat missing shell context as permission to silently drop the parent-child relationship. If the current parent cannot be identified confidently, ask the user for the thread ID.

BB has no CLI max-depth flag, so every delegated prompt must state the role, allowed depth, and prohibition on further delegation where applicable.

### Spawn the direct child

```bash
# Preferred when BB_THREAD_ID is available
bb thread spawn --parent-self --project <project-id> \
  --title "Fix login bug" --new-environment worktree --visibility visible \
  --prompt "<role/depth preamble + subagent-delegation brief>"

# Equivalent when the verified parent ID is explicit
bb thread spawn --parent-thread <parent-thread-id> --project <project-id> \
  --title "Fix login bug" --new-environment worktree --visibility visible \
  --prompt "<role/depth preamble + subagent-delegation brief>"

# Equivalent when assigning work in another project while retaining the same parent
bb thread spawn --parent-thread <parent-thread-id> --project proj_iekidk5qz8 --visibility visible \
  --prompt "<role/depth preamble + subagent-delegation brief>"
```

Rules:
- **Always pass `--project` explicitly** — the CLI never infers it.
- `--parent-self` and `--parent-thread <verified-id>` are equivalent native child-thread routes. Prefer explicit `--parent-thread` when shell context is missing or uncertain.
- Omit the parent flag only for intentionally independent root work—not as a fallback for missing environment variables.
- Use `--visibility visible` for normal workers so their cards and sidebar entries appear in BB. Never use `hidden` for work the user should monitor.
- A child with a non-null `parentThreadId` must not delegate unless the selected agent prompt explicitly assigns a bounded exception. Invoked skills own any provider-native subagents their contracts require; do not create nested BB threads beyond the selected agent's explicit topology.
- Child permission is capped by the parent's mode. `--permission-mode` options: `accept-edits`, `auto` (default), `full`.
- For review/fix follow-ups on the *same* files: get env id from `bb thread show <id> --json`, then `--environment <env-id>`.
- Use `--new-environment worktree` only for a Git repo with at least one commit. For same-checkout work, pass the verified parent's `environment.id` explicitly with `--environment <environment-id>`; use `$BB_ENVIRONMENT_ID` only when it is actually set.
- **Don't poll.** Use `bb thread wait <id>` to block (it may be silent while waiting), or let lifecycle notifications arrive.
- Steer/queue follow-ups: `bb thread tell <id> "..."` (steers by default; `--mode queue` for non-urgent).
- Inspect results: `bb thread show <id>`, `bb thread show <id> --git-diff`, `bb thread output <id>`.
- Stop stuck/finished hidden workers: `bb thread stop <id>`.
- When this router permits delegation, load and follow `subagent-delegation`. Keep BB role/depth constraints as the preamble; do not restate the skill's templates here.

---

## 5. Common Actions → BB Commands (cheat sheet)

| Action | Command |
| --- | --- |
| Orient: current project/thread/env | `bb status` |
| List projects / machines | `bb project list [--include-personal]` / `bb machine list` |
| List providers & models | `bb provider list`, `bb provider models <provider-id>` |
| Delegate a task | Root coordinator: `bb thread spawn --parent-self ...` or `bb thread spawn --parent-thread <verified-parent-id> ...` |
| Wait for / message a thread | `bb thread wait <id>`, `bb thread tell <id> "..."` |
| Review a thread's work | `bb thread show <id> --git-diff`, `bb thread log <id>` |
| Read/write files on host | `bb file read\|write\|list` (`--root` confines mutations) |
| Long-running command (dev server) | `bb terminal create --thread <id> --command "pnpm dev"` |
| Plan-first delegation | `bb thread spawn ... --plan` |
| Schedule work | `bb automation create --project <id> --name "..." --cron "..." ...` |
| List/install skills | `bb skill list`, `bb skill search <q>`, `bb skill install <id>` |
| Read/edit a skill | `bb skill show <id>`, `bb skill files <id>` |
| Secrets into a dotenv | `bb secret request <NAME> --write-env <path>` |
| Open artifact for user in IDE | `bb thread open <path>` |

---

## 6. Router — When to Use What

| Situation | Do this |
| --- | --- |
| Multi-step or parallelizable work | Root coordinator spawns native direct children; terminal workers never delegate without an explicit selected-agent exception |
| Work in a specific repo | Spawn with that repo's `--project <id>` |
| Work that shouldn't touch the repo / needs isolation | `--new-environment worktree` |
| Quick question or 1-file change | Do it yourself; don't spawn |
| Long-running process (server, watch) | `bb terminal` — a real PTY the user can see and stop |
| Recurring / scheduled work | `bb automation create` (script mode for deterministic checks, agent mode for reasoning) |
| Recalled context needed | `bb thread search`, `bb thread log --all`, or memory plugin (`bb memory search`) |
| Need another agent | Root coordinator uses a native direct child; other workers report the need unless their selected agent prompt grants a bounded exception |
| Unknown host detail | Check `~/SYSTEMS.md` first, then `bb guide` |

---

## 7. Plugin Work — Reference Resources

When working on BB plugins, consult these for shape, architecture, and current implementations:

- https://github.com/get-bb/marketplace
- https://github.com/MGrin/awesome-bb-plugins

---

## 8. House Rules

- Don't run a second BB instance against the same data dir. Restart per `~/SYSTEMS.md`.
- `~/SYSTEMS.md` documents private Tailscale-only services — never publish URLs or credentials.
- BB injects this file first, then an optional `<workspace>/.bb/AGENTS.md` for project-specific additions.
