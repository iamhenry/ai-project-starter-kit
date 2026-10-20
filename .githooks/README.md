# Git hooks

Two checks, one file each, so you can tune or drop either without touching the other:

| File | Blocks | Runs on |
|---|---|---|
| `checks/size.sh` | source files over 5,000 tokens (bytes / 4); markdown exempt | staged files, at commit |
| `checks/secrets.sh` | API keys, private keys, committed `.env` files | staged files at commit; every commit being pushed |
| `commit-msg` | keys pasted into the commit message | every commit message |

`pre-commit` runs both checks. `commit-msg` runs the secret rules over the
message text. `pre-push` runs blocking secret rules only — size is a
commit-time concern, publishing is the one that cannot be undone.

## Enable

Once per clone (hooks are not cloned with the repo):

```sh
git config core.hooksPath .githooks
```

Check it: `git config core.hooksPath`. Turn it off: `git config --unset core.hooksPath`.

## Use these hooks in every project on this machine

Set the hooks path once, globally, to this folder in the main checkout:

```sh
git config --global core.hooksPath /Users/macvm/Desktop/Projects/other/ai-project-starter-kit/.githooks
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

Both checks look only at what you are about to publish: the secret scan reads
added lines in patches, and the size check measures the whole staged file.

Detected, with high confidence: provider keys with fixed shapes, PEM private-key
blocks, three-part JWTs, and credentials embedded in URLs. The matched value is
never printed — you get a path, a line and a rule name.

A committed `.env` is blocked on sight, whatever it contains — its values are
random enough to look like nothing in particular, so no pattern rule would
reliably find them. `.env.example`, `.env.sample` and `.env.template` are fine.

Commit messages are scanned the same way, because a key pasted into a message
is published exactly like one in a file.

Warned, not blocked: private IP ranges, `*.ts.net` hosts, `/Users/<name>` paths,
email addresses. Warnings appear at commit time only.

**Not detected:** unprefixed random tokens; values built at runtime or split
across lines; secrets inside binaries, archives or databases; anything that does
not look like a known key shape. Treat this as a net for copy-paste accidents,
not as proof that a commit is clean.

`pre-push` scans every commit not already on a remote, merge commits included,
so a key that was added and later removed is still caught. A key that was already pushed is not
recoverable by any hook — rotate it.

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
