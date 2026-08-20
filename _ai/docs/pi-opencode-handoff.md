# Pi / OpenCode handoff

Merged. Agents/skills live in `.agents/` (shared by Pi + OpenCode). Commands are OpenCode-only.

No OpenCode env var. It already reads `~/.config/opencode/{agent,command,skills}` (singular names still work).

## Other machine (same setup)

Pull `main`. Set `KIT` to this clone. Then run:

```bash
KIT="$HOME/Desktop/Projects/other/ai-project-starter-kit"

# OpenCode — retarget the 3 dangling links. plugin + opencode.jsonc stay as-is.
ln -sfn "$KIT/.agents/agents"   "$HOME/.config/opencode/agent"
ln -sfn "$KIT/.agents/commands" "$HOME/.config/opencode/command"
ln -sfn "$KIT/.agents/skills"   "$HOME/.config/opencode/skills"

# Pi — backup first, then link kit files. Theme (dark) lives in kit settings.json.
cp "$HOME/.pi/agent/settings.json" "$HOME/.pi/agent/settings.json.bak.$(date +%Y%m%d%H%M%S)"
ln -sfn "$KIT/.pi/settings.json" "$HOME/.pi/agent/settings.json"
mkdir -p "$HOME/.pi/agent/extensions"
ln -sfn "$KIT/.pi/extensions/safety.ts" "$HOME/.pi/agent/extensions/safety.ts"
ln -sfn "$KIT/.pi/scripts/patch-open-agents.sh" "$HOME/.pi/agent/patch-open-agents.sh"
ln -sfn "$KIT/.pi/scripts/pi-update.sh" "$HOME/.pi/agent/pi-update.sh"
```

Leave **local** (do not symlink, do not commit):

```text
~/.pi/agent/auth.json
~/.pi/agent/trust.json
~/.pi/agent/models-store.json
~/.pi/agent/sessions/
~/.pi/agent/npm/
```

Do **not** global-link `.pi/agents/explorer.md`. That only disables bundled `explorer` in this repo.

Pi may write `lastChangelogVersion` into kit `.pi/settings.json` through the symlink. Drop it; do not commit it.

## Check

```bash
ls -l ~/.config/opencode/{agent,command,skills,plugin}
ls -l ~/.pi/agent/settings.json ~/.pi/agent/extensions/safety.ts ~/.pi/agent/{patch-open-agents,pi-update}.sh
```

Then: open OpenCode in another project — agents, `/commands`, skills, `plan` denylist. Restart Pi — packages + `safety.ts`.

## Still true

- `pi-open-agents` subagents are **blocking**. Do not install `pi-subagent-lite` beside it.
- Two Codex accounts: Pi native auth is one credential. Manual: `@narumitw/pi-accounts`. Auto-rotate: `pi-multi-account` — not installed.
- Keep `.pi/scripts/pi-update.sh` until https://github.com/andrea-tomassi/pi-open-agents/pull/7 lands, then drop the local patch.
- Project Pi extensions load only after this folder is trusted.
- Slash commands are not shared with Pi (`.agents/commands` vs `.pi/prompts`). Do not set `"prompts": [".agents/commands"]` and expect nested `/git` commands.

## Do not

- Copy `.agents` into every other repo.
- Point other projects at `.agents` unless they also run Pi.
- Run Lite + `pi-open-agents` in the same Pi process.
- Add repo shims under `.opencode/{agent,command,skills}`. Global retarget is the setup.
