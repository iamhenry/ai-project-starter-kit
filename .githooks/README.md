# Git hooks

Two checks, one file each, so you can tune or drop either without touching the other:

| File | Blocks | Runs on |
|---|---|---|
| `checks/size.sh` | source files over 5,000 tokens (bytes / 4); markdown exempt | staged files, at commit |
| `checks/secrets.sh` | built-in API-key and private-key rules, committed `.env` files, private-detail warnings | staged files at commit; every commit being pushed |
| `checks/private.sh` | home paths, BB IDs, real emails, private hosts, trace files, ignored files and large files | every commit being pushed |
| `gitleaks` | broader secret patterns; values are hidden in hook output | staged files at commit; every commit being pushed, when installed |
| `commit-msg` | keys pasted into the commit message | every commit message |

`pre-commit` runs the size check, the built-in rules and gitleaks. `commit-msg`
runs the built-in secret rules over the message text. `pre-push` runs blocking
secret checks on every commit being published — size is a commit-time concern,
publishing is the one that cannot be undone.

Gitleaks is optional. If it is not on `PATH`, the hook prints a loud warning
with `brew install gitleaks` and continues with the built-in rules. Installing
it is each person's choice and needs their approval; the hook never installs
software. If gitleaks is present but cannot scan, the hook blocks as a precaution.

## Enable

Once per clone (hooks are not cloned with the repo):

```sh
git config core.hooksPath .githooks
```

Check it: `git config core.hooksPath`. Turn it off: `git config --unset core.hooksPath`.

## Use these hooks in every project on this machine

Set the hooks path once, globally, to this folder in the main checkout:

```sh
git config --global core.hooksPath ~/Desktop/Projects/other/ai-project-starter-kit/.githooks
```

This adds one line to `~/.gitconfig`. It changes no files and touches no repo.
Every repo and worktree that doesn't set its own hooks path then runs these
hooks. Edit a script here, merge to `main`, and all projects get the update.

- **Keep the main checkout on `main`.** Other projects run whatever branch is
  checked out in that folder.
- **Use the main checkout path, not a worktree path.** Worktrees get deleted.
- **A repo's own `core.hooksPath` overrides the global one** (for example
  husky's `.husky/_`), so the checks do not run there. Find these repos with
  `git config --local --get core.hooksPath` inside the repo. If it prints
  something, the repo overrides the global setting.
- **With a global path set, Git ignores each repo's `.git/hooks`.**
- **This covers your machine only.** Teammates and CI do not get the hooks.

Commands:

- See the global setting: `git config --global --get core.hooksPath`
- See where a repo's value comes from: `git config --show-origin --get core.hooksPath`
- Undo: `git config --global --unset core.hooksPath`

## What it actually covers

The secret scanners check changes being committed or pushed. They read added
lines in patches. The size check measures the whole staged file at commit time.

The built-in scanner detects provider keys with fixed shapes, PEM private-key
blocks, three-part JWTs, and credentials embedded in URLs. When installed,
gitleaks adds its maintained set of secret patterns. For both scanners, the
matched value is never printed — you get a path, a line and a rule name.

A committed `.env` is blocked on sight, whatever it contains — its values are
random enough to look like nothing in particular, so no pattern rule would
reliably find them. `.env.example`, `.env.sample` and `.env.template` are fine.

Commit messages are scanned the same way, because a key pasted into a message
is published exactly like one in a file.

At push time, a guard checks only lines added by commits being pushed, in every
repo, public or private. Old history does not block a push. It blocks these
rules: `home-path` (`/Users/<name>` and `/home/<name>`), `bb-id` (thread and
project IDs with `thr_` or `proj_` plus 10 lowercase letters or digits, and
session IDs with `ses_` plus 24 or more characters), `email` (real-looking
addresses; `user@example.com`, `user@example.org`, `user@example.net`,
`user@example.invalid`, `user@name.example`, `user@name.invalid`,
`user@name.test`, `user@name.localhost`, and `git@github.com` pass),
`private-host` (`*.ts.net` except `example.ts.net`, and this machine's hostname
read when the hook runs), `trace-file` (`*.jsonl`, `*.ndjson`, or paths with a
`traces/`, `transcripts/`, or `sessions/` folder), `ignored-file` (a force-added
path ignored by this repo's `.gitignore`), and `large-file` (over 200 KB).

At commit time, these private-detail checks remain warnings; private IPs also
remain warnings. `.githooks/skip` exempts line rules only. Path rules
(`trace-file`, `ignored-file`, `large-file`) need an exception in the repo-root
`.githooks-allow` file. Each line must have a path or glob, rule, and reason:
`<path-or-glob> <rule> # reason`. A line without a reason is ignored and
reported. For example: `fixtures/sample.jsonl trace-file # synthetic test data, no real users`.
This file cannot exempt API keys or `.env` files. The guard never prints matched
text. If the guard fails, the push is blocked.

Run the guard tests with `bash .githooks/tests/push-guard.sh`.

**Not guaranteed detected:** unprefixed random tokens; values built at runtime
or split across lines; secrets inside binaries, archives or databases; anything
that does not look like a known key shape. Treat these checks as a net for
copy-paste accidents, not as proof that a commit is clean.

`pre-push` scans added lines in commits being pushed, merge commits included.
A key that was already pushed is not recoverable by any hook — rotate it.

Local overrides exist and are deliberate: `--no-verify`, `SKIP_HOOKS=1`, and
`core.hooksPath` unset all bypass both hooks. Without an equivalent CI job
running `checks/secrets.sh`, there is no guarantee a secret stays off the remote.

## Tune

- **A file is legitimately large** — add a glob to `.githooks/skip`. Lockfiles,
  `dist/`, vendored code and assets are already there.
- **A secret is a deliberate example** — append `pragma: allowlist secret` to
  that line.
- **Prose is exempt** — `.md` and `.mdx` skip the token budget entirely. Secrets
  are still scanned inside them.
- **A tracked `.env` is intentional** — add `.env` to `.githooks/skip`.
- **Different budget** — `LIMIT_TOKENS=2000 git commit`.
- **Skip once** — `SKIP_HOOKS=1 git commit` / `git push`.

## Adding a rule

Append `name<space>regex` to `BLOCK_RULES` or `WARN_RULES` in
`checks/secrets.sh`. Anything that fails to run — bad regex, unreadable
history — blocks the commit rather than passing silently.
