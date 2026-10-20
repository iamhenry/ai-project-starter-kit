#!/usr/bin/env bash
# Blocks API keys and private keys. Warns, but allows, on private addresses
# and personal details. Extend the rule lists below; both are
# "name<space>regex", one rule per line.
#
# Usage: secrets.sh staged                  (the index)
#        secrets.sh push <base> <head>      (every commit being published)
#        secrets.sh message <file>           (a commit message)
#
# It scans patches, not files: only added lines can introduce a credential,
# and a secret committed then deleted still shows up as an added line in the
# commit that introduced it. Merges are diffed against each parent (-m) so a
# key typed during conflict resolution is caught too.
#
# Patches and commit messages are read as two separate streams. A message line
# that looks like a diff header must never be able to steer the patch parser.
#
# The matched text is never printed: a blocked secret must not land in
# terminal scrollback or an agent transcript. Location and rule name are enough.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
SKIP_FILE="$here/../skip"
# shellcheck source=lib.sh
. "$here/lib.sh"

BLOCK_RULES='private-key -----BEGIN [A-Z ]*PRIVATE KEY-----
aws-access-key AKIA[0-9A-Z]{16}
github-token gh[pousr]_[A-Za-z0-9]{36,}
github-pat github_pat_[A-Za-z0-9_]{22,}
openai-key sk-[A-Za-z0-9_-]{20,}
stripe-live sk_live_[A-Za-z0-9]{16,}
slack-token xox[baprs]-[A-Za-z0-9-]{10,}
google-api-key AIza[0-9A-Za-z_-]{30,}
jwt eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}
url-credentials ://[^/[:space:]:@]+:[^/[:space:]:@]+@'

WARN_RULES='private-ip (^|[^0-9.])((10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|(192\.168\.[0-9]{1,3}\.[0-9]{1,3})|(172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}))([^0-9]|$)
tailscale-host [A-Za-z0-9-]+\.ts\.net
home-dir /Users/[A-Za-z0-9._-]+/
email [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

# Reads either a patch stream (default) or a message stream (SCAN_MODE=message).
# In message mode every line is content except our own \001<hash> header.
AWK_PROG='
  function unquote(s,   out, i, c, n, oct, k) {
    if (substr(s, 1, 1) != "\"") return s
    n = length(s)
    s = (substr(s, n, 1) == "\"") ? substr(s, 2, n - 2) : substr(s, 2)
    out = ""
    for (i = 1; i <= length(s); i++) {
      c = substr(s, i, 1)
      if (c != "\\") { out = out c; continue }
      i++
      c = substr(s, i, 1)
      if (c == "n") out = out "\n"
      else if (c == "t") out = out "\t"
      else if (c == "r") out = out "\r"
      else if (c ~ /[0-7]/) {
        oct = c; k = 0
        while (k < 2 && substr(s, i + 1, 1) ~ /[0-7]/) { i++; oct = oct substr(s, i, 1); k++ }
        out = out sprintf("%c", oct + 0)
      } else out = out c
    }
    return out
  }
  function scanbody(body, pth, ln,   i, rest, m, lm) {
    for (i = 1; i <= nb; i++) {
      rest = body
      while (match(rest, br[i])) {
        if (RLENGTH == 0) break
        m = substr(rest, RSTART, RLENGTH)
        rest = substr(rest, RSTART + RLENGTH)
        if (bn[i] == "url-credentials") {
          lm = tolower(m)
          if (lm ~ /^:\/\/(user|username|<user>):(pass|password|pwd|<password>|<token>|token)@$/) continue
          if (index(m, "${") > 0) continue
        }
        printf "B\037%s\037%s\037%s\037%s\n", bn[i], commit, pth, ln
      }
    }
    for (i = 1; i <= nw; i++) {
      if (!match(body, wr[i])) continue
      printf "W\037%s\037%s\037%s\037%s\n", wn[i], commit, pth, ln
    }
  }
  BEGIN {
    nb = split(ENVIRON["BLOCK_RULES"], rb, "\n")
    for (i = 1; i <= nb; i++) {
      if (rb[i] == "") continue
      p = index(rb[i], " ")
      bn[i] = substr(rb[i], 1, p - 1); br[i] = substr(rb[i], p + 1)
    }
    nw = split(ENVIRON["WARN_RULES"], rw, "\n")
    for (i = 1; i <= nw; i++) {
      if (rw[i] == "") continue
      p = index(rw[i], " ")
      wn[i] = substr(rw[i], 1, p - 1); wr[i] = substr(rw[i], p + 1)
    }
  }
  ENVIRON["SCAN_MODE"] == "message" {
    if (substr($0, 1, 1) == "\001") { commit = substr($0, 2); mline = 0; next }
    mline++
    scanbody($0, "(commit message)", mline)
    next
  }
  /^commit / { commit = $2; state = "head"; path = ""; next }
  /^diff --git / { state = "head"; path = ""; next }
  state == "head" && /^\+\+\+ / {
    path = unquote(substr($0, 5)); sub(/^b\//, "", path); next
  }
  /^@@ / {
    state = "hunk"
    split($0, pp, "+"); split(pp[2], qq, /[, ]/); line = qq[1] - 1
    next
  }
  state == "hunk" && substr($0, 1, 1) == "+" {
    body = substr($0, 2)
    line++
    if (body ~ /pragma: allowlist secret/) next
    scanbody(body, path, line)
    next
  }
'
export BLOCK_RULES WARN_RULES

mode=${1:?usage: secrets.sh staged | secrets.sh push <base> <head> | secrets.sh message <file>}
tmp=$(mktemp "${TMPDIR:-/tmp}/hookpatch.XXXXXX")
msg=$(mktemp "${TMPDIR:-/tmp}/hookmsg.XXXXXX")
names=$(mktemp "${TMPDIR:-/tmp}/hooknames.XXXXXX")
err=$(mktemp "${TMPDIR:-/tmp}/hookerr.XXXXXX")
trap 'rm -f "$tmp" "$msg" "$names" "$err"' EXIT

fail() {
  printf '\n  ✗ secret scan could not run: %s\n' "$1"
  printf '    Nothing was checked for this step, so it is blocked as a precaution.\n'
  printf '    Fix the scanner, or override once: SKIP_HOOKS=1 git ...\n\n'
  exit 2
}

RANGE=()
case $mode in
  staged)
    PATCH_CMD=(git -c core.quotePath=false diff --cached -U0 --no-color --no-ext-diff --no-textconv --diff-filter=ACMR)
    NAME_CMD=(git -c core.quotePath=false diff --cached --name-only -z --diff-filter=ACMR)
    ;;
  push)
    base=${2:-}
    head=${3:-}
    [ -n "$head" ] || fail "missing push target"
    if [ -n "$base" ] && [ -z "$(printf %s "$base" | tr -d 0)" ]; then
      RANGE=("$head" --not --remotes)   # new branch: everything not already public
    else
      RANGE=("$base..$head")
    fi
    PATCH_CMD=(git -c core.quotePath=false log -p -m -U0 --no-color --no-ext-diff --no-textconv --format='commit %h' "${RANGE[@]}")
    NAME_CMD=(git -c core.quotePath=false log --name-only -z -m --format= --diff-filter=ACMR "${RANGE[@]}")
    MSG_CMD=(git -c core.quotePath=false log -m --format='%x01%h%n%B' "${RANGE[@]}")
    ;;
  message)
    printf '\001commit-msg\n' >"$msg"
    cat "${2:-}" >>"$msg" 2>"$err" || fail "could not read the message file"
    ;;
  *)
    fail "unknown mode '$mode'"
    ;;
esac

blocked=0
warned=0

# A committed .env is a leak whatever it contains: its values do not look like
# any known key shape. Checked by path, so renames and binary files count.
if [ "$mode" != "message" ]; then
  "${NAME_CMD[@]}" >"$names" 2>>"$err" || fail "$(head -1 "$err")"
  while IFS= read -r -d '' p; do
    [ -z "$p" ] && continue
    case $p in
      *.env.example|*.env.sample|*.env.template) continue ;;
      .env|.env.*|*/.env|*/.env.*) ;;
      *) continue ;;
    esac
    skipped "$p" && continue
    printf '  ✗ %s  env-file\n' "$p"
    blocked=$((blocked + 1))
  done <"$names"
fi

hits=""
if [ "$mode" = "message" ]; then
  hits=$(SCAN_MODE=message awk "$AWK_PROG" "$msg") ||
    fail "rule evaluation failed — check the regex lists in this file"
else
  "${PATCH_CMD[@]}" >"$tmp" 2>"$err" || fail "$(head -1 "$err")"
  hits=$(SCAN_MODE=patch awk "$AWK_PROG" "$tmp") ||
    fail "rule evaluation failed — check the regex lists in this file"
  if [ "$mode" = "push" ]; then
    "${MSG_CMD[@]}" >"$msg" 2>>"$err" || fail "$(head -1 "$err")"
    hits="$hits
$(SCAN_MODE=message awk "$AWK_PROG" "$msg")" ||
      fail "rule evaluation failed on commit messages"
  fi
fi

while IFS=$'\037' read -r kind name commit path line; do
  [ -z "$kind" ] && continue
  skipped "$path" && continue
  where=$path:$line
  [ -n "$commit" ] && where="$commit  $path:$line"
  if [ "$kind" = "B" ]; then
    printf '  ✗ %s  %s\n' "$where" "$name"
    blocked=$((blocked + 1))
  else
    printf '  ! %s  %s\n' "$where" "$name"
    warned=$((warned + 1))
  fi
done <<< "$(printf '%s\n' "$hits" | sort -u)"

if [ "$blocked" -gt 0 ]; then
  cat <<EOF

  $blocked secret(s) found. Blocked.

    Fix it:
      1. Delete the value from the file.
      2. Rotate the key — assume it is already leaked.
      3. Load it from the environment instead: process.env.NAME
      4. Real value goes in .env (gitignored); a placeholder goes in .env.example.
    Committed a .env? git rm --cached it and add it to .gitignore.
    Deliberate example? Add "pragma: allowlist secret" to that line.
    One-off override: SKIP_HOOKS=1 git ...
    Already in a commit? Rewrite that commit before pushing, then rotate anyway.

EOF
  exit 1
fi

if [ "$warned" -gt 0 ]; then
  printf '\n  %s private detail(s) above. Not blocked — check they belong here.\n\n' "$warned"
fi
exit 0
