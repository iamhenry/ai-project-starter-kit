# Pi / OpenCode handoff

Branch: `feat/pi-agent-migration`
Do not merge to `main` until global OpenCode links are retargeted and Pi configs are linked global.

## Done

- Agents and skills live in `.agents/` so Pi and OpenCode share them. Commands are still OpenCode-only.
- `.pi/settings.json` lists `pi-open-agents`, `pi-multimodal-proxy`, `pi-ollama-cloud`.
- `.pi/extensions/safety.ts` blocks secret file access and catastrophic bash for all Pi agents/children.
- `.pi/scripts/patch-open-agents.sh` forces `pi-open-agents` to scan `.agents/agents` only (not skills).
- Upstream: https://github.com/andrea-tomassi/pi-open-agents/pull/7
- Project PR: https://github.com/iamhenry/ai-project-starter-kit/pull/59

## Breaks other projects on merge

`~/.config/opencode` still points at the **main checkout**:

```text
agent    -> .../ai-project-starter-kit/.opencode/agent
command  -> .../ai-project-starter-kit/.opencode/command
skills   -> .../ai-project-starter-kit/.opencode/skills
plugin   -> .../ai-project-starter-kit/.opencode/plugin   # still valid
opencode.jsonc -> .../ai-project-starter-kit/opencode.jsonc
```

This branch deletes `.opencode/{agent,command,skills}`. Those 3 links go dangling. Every other repo that inherits global OpenCode loses agents, commands, and skills.

`opencode.jsonc` also lost `build` / `plan` / `general` JSON. Those now live in `.agents/agents/*.md`.

## Same-day as merge: make Pi configs global

Same pattern as OpenCode: the **main checkout** is the source of truth. After merge, symlink Pi files into `~/.pi/agent/` so every project inherits them.

KIT=`/Users/macvm/Desktop/Projects/other/ai-project-starter-kit`

```text
~/.pi/agent/settings.json              -> $KIT/.pi/settings.json
~/.pi/agent/extensions/safety.ts       -> $KIT/.pi/extensions/safety.ts
~/.pi/agent/patch-open-agents.sh       -> $KIT/.pi/scripts/patch-open-agents.sh
~/.pi/agent/pi-update.sh               -> $KIT/.pi/scripts/pi-update.sh
```

Back up any existing global `settings.json` first. Then:

```bash
ln -sfn "$KIT/.pi/settings.json" "$HOME/.pi/agent/settings.json"
mkdir -p "$HOME/.pi/agent/extensions"
ln -sfn "$KIT/.pi/extensions/safety.ts" "$HOME/.pi/agent/extensions/safety.ts"
ln -sfn "$KIT/.pi/scripts/patch-open-agents.sh" "$HOME/.pi/agent/patch-open-agents.sh"
ln -sfn "$KIT/.pi/scripts/pi-update.sh" "$HOME/.pi/agent/pi-update.sh"
```

Leave these **local** (secrets / machine / generated):

```text
~/.pi/agent/auth.json
~/.pi/agent/trust.json
~/.pi/agent/models-store.json
~/.pi/agent/sessions/
~/.pi/agent/npm/
```

Do **not** global-link `.pi/agents/explorer.md`. That only disables bundled `explorer` in this repo.

After linking, restart Pi in another project and confirm packages + `safety.ts` load.

## Problem: slash commands are not shared

`.agents/commands` is OpenCode. Pi slash commands are `.pi/prompts` (non-recursive). Same markdown folder is not enough:

- Nested files (`git/`, `workflow/`) do not become Pi `/` commands.
- Pi ignores `name`, `agent`, `model`, `subtask`.
- Bodies say `Task`; Pi’s tool is `subagent`.

Naive first try if we iterate later:

```json
"prompts": [".agents/commands"]
```

That only sees top-level files like `/debug`. Not a real dual-command setup.

## Remaining

1. **Same-day as merge — OpenCode links, pick one**
   - Retarget global links (keep singular names):
     ```text
     ~/.config/opencode/agent    -> .../.agents/agents
     ~/.config/opencode/command  -> .../.agents/commands
     ~/.config/opencode/skills   -> .../.agents/skills
     ```
   - Or add repo shims so old links keep working:
     ```text
     .opencode/agent   -> ../.agents/agents
     .opencode/command -> ../.agents/commands
     .opencode/skills  -> ../.agents/skills
     ```
2. After merge, open OpenCode in another project and confirm agents, `/commands`, skills, and `plan` denylist still load.
3. `pi-open-agents` subagents are **blocking**. Do not install `pi-subagent-lite` beside it (same `subagent` tool, different schema, no `.agents` discovery, ignores `permission:`).
4. Two Codex accounts: Pi native auth is one credential. Manual: `@narumitw/pi-accounts`. Auto-rotate: `pi-multi-account` — not installed; policy-sensitive.
5. Keep using `.pi/scripts/pi-update.sh` until upstream PR 7 lands, then drop the local patch.
6. Never commit `auth.json`, `trust.json`, `sessions/`, `npm/`, `models-store.json`.
7. Project Pi extensions load only after this folder is trusted.

## Do not

- Copy `.agents` into every other repo.
- Point other projects at `.agents` unless they also run Pi.
- Run Lite + `pi-open-agents` in the same Pi process.
