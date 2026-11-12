#!/usr/bin/env bash
# Blocks private details and risky files in commits being pushed.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
SKIP_FILE="$here/../skip"
. "$here/lib.sh"
fail() {
  printf 'private-detail check could not run: %s. Nothing was checked, so the push is blocked.\n' "$1"
  exit 2
}
base=${1:-}; head=${2:-}
[ -n "$head" ] || fail 'missing push target'
if [ -n "$base" ] && [ -z "$(printf %s "$base" | tr -d 0)" ]; then range=("$head" --not --remotes); else range=("$base..$head"); fi
git rev-parse --verify "$head^{commit}" >/dev/null 2>&1 || fail 'invalid push range'
if [ -n "$base" ] && [ -z "$(printf %s "$base" | tr -d 0)" ]; then :; else git rev-parse --verify "$base^{commit}" >/dev/null 2>&1 || fail 'invalid push range'; fi
tmp=$(mktemp -d "${TMPDIR:-/tmp}/private-hook.XXXXXX") || fail 'could not create temporary files'
trap 'rm -rf "$tmp"' EXIT
git -c core.quotePath=false log -p -m -U0 --no-color --no-ext-diff --no-textconv --format='commit %h' "${range[@]}" >"$tmp/patch" 2>/dev/null || fail 'git could not read pushed changes'
hostname=$(hostname -s 2>/dev/null || true)
host_re=''
if [ "${#hostname}" -ge 4 ] && [ "$hostname" != localhost ]; then host_re=$(printf '%s' "$hostname" | sed 's/[][\\.^$*+?(){}|]/\\&/g'); fi
export host_re
awk '
  /^commit / { commit=$2; state="head"; path="" }
  /^diff --git / { state="head"; path="" }
  state == "head" && /^\+\+\+ / { path=substr($0,7); sub(/^b\//,"",path) }
  /^@@ / { state="hunk"; p=index($0,"+"); h=substr($0,p+1); split(h,b,/[, ]/); line=b[1]-1 }
  state == "hunk" && substr($0,1,1) == "+" {
      line++; text=substr($0,2); if (text ~ /pragma: allowlist secret/) next
    if (text ~ /\/Users\/[A-Za-z0-9._-]+(\/|[^A-Za-z0-9._-]|$)/ || text ~ /\/home\/[A-Za-z0-9._-]+(\/|[^A-Za-z0-9._-]|$)/) print commit "\t" path ":" line "\thome-path"
    if (text ~ /(^|[^[:alnum:]_])(thr_|proj_)[a-z0-9]{10}([^[:alnum:]_]|$)/ || text ~ /(^|[^[:alnum:]_])ses_[A-Za-z0-9]{24,}([^[:alnum:]_]|$)/) print commit "\t" path ":" line "\tbb-id"
    rest=text; badmail=0
    while (match(rest,/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z0-9.-]+/)) {
      addr=substr(rest,RSTART,RLENGTH); rest=substr(rest,RSTART+RLENGTH)
      split(addr,parts,"@"); user=parts[1]; domain=tolower(parts[2])
      if (user=="pkg" && domain ~ /^[0-9.]+$/) continue
      if (user=="git") continue
      if (domain ~ /(^|[.])example([.]|$)/ || domain ~ /(^|[.])invalid([.]|$)/ || domain ~ /(^|[.])test([.]|$)/ || domain ~ /(^|[.])localhost([.]|$)/) continue
      badmail=1
    }
    if (badmail) print commit "\t" path ":" line "\temail"
    if (text ~ /[[:alnum:].-]+[.]ts[.]net/ && text !~ /example[.]ts[.]net/) print commit "\t" path ":" line "\tprivate-host"
    if (ENVIRON["host_re"] != "") { low=tolower(text); host=tolower(ENVIRON["host_re"]); pos=1; while (match(substr(low,pos),host)) { at=pos+RSTART-1; before=(at>1 ? substr(low,at-1,1) : ""); after=substr(low,at+length(host),1); if (before !~ /[[:alnum:]_]/ && after !~ /[[:alnum:]_]/) { print commit "\t" path ":" line "\tprivate-host"; break } pos=at+length(host) } }
  }
' "$tmp/patch" >"$tmp/hits" 2>"$tmp/awkerr" || fail 'rule evaluation failed'
blocked=0
allow=$(git rev-parse --show-toplevel)/.githooks-allow
allowed() {
  local target=$1 rule=$2 pat want reason
  [ -f "$allow" ] || return 1
  while IFS= read -r entry || [ -n "$entry" ]; do
    case "$entry" in ''|\#*) continue ;; esac
    [[ "$entry" == *'#'* ]] || continue
    left=${entry%%#*}; reason=${entry#*#}; [ -n "${reason//[[:space:]]/}" ] || continue
    read -r pat want _ <<<"$left"
    [ "$want" = "$rule" ] || continue
    case "$target" in $pat) return 0 ;; esac
  done <"$allow"
  return 1
}
while IFS=$'\t' read -r commit loc rule; do
  [ -n "$rule" ] || continue
  path=${loc%:*}; skipped "$path" && continue
  allowed "$path" "$rule" && continue
  printf '  ✗ %s  %s  %s\n' "$commit" "$loc" "$rule"; blocked=1
done <"$tmp/hits"
git -c core.quotePath=false log --name-only -z -m --format= --diff-filter=ACMR "${range[@]}" >"$tmp/paths" 2>/dev/null || fail 'git could not read pushed paths'
while IFS= read -r -d '' path; do
  [ -n "$path" ] || continue
  rule=''
  case "/$path/" in */traces/*|*/transcripts/*|*/sessions/*) rule=trace-file ;; esac
  case "$path" in *.jsonl|*.ndjson) rule=trace-file ;; esac
  if [ -n "$rule" ] && ! allowed "$path" "$rule"; then printf '  ✗ %s  %s\n' "$path" "$rule"; blocked=1; fi
  if git check-ignore --no-index -q -- "$path"; then
    if ! allowed "$path" ignored-file; then printf '  ✗ %s  ignored-file\n' "$path"; blocked=1; fi
  else
    rc=$?; [ "$rc" -eq 1 ] || fail 'git could not check ignored files'
  fi
done <"$tmp/paths"
# Check each pushed commit's changed blobs; this avoids relying on the working tree.
git rev-list "${range[@]}" >"$tmp/commits" 2>/dev/null || fail 'git could not list pushed commits'
while read -r commit; do
  git diff-tree --root --no-commit-id --name-only -r -m -z --diff-filter=ACMR "$commit" >"$tmp/blobpaths" 2>/dev/null || fail 'git could not inspect pushed blobs'
  while IFS= read -r -d '' path; do
    blob=$(git rev-parse "$commit:$path" 2>/dev/null) || fail 'git could not inspect pushed blobs'
    size=$(git cat-file -s "$blob" 2>/dev/null) || fail 'git could not inspect pushed blobs'
    if [ "$size" -gt 204800 ] && ! allowed "$path" large-file; then printf '  ✗ %s  large-file\n' "$path"; blocked=1; fi
  done <"$tmp/blobpaths"
done <"$tmp/commits"
if [ -f "$allow" ]; then
  n=0
  while IFS= read -r entry || [ -n "$entry" ]; do
    n=$((n+1)); case "$entry" in ''|\#*) continue ;; esac
    if [[ "$entry" != *'#'* || -z "${entry#*#}" || -z "${entry#*#}" || -z "$(printf %s "${entry#*#}" | tr -d '[:space:]')" ]]; then printf '  ! .githooks-allow:%s ignored: no reason\n' "$n"; fi
  done <"$allow"
fi
[ "$blocked" -eq 0 ] || { printf 'Private-detail check blocked this push. Fix the findings or add a reasoned .githooks-allow exception.\n'; exit 1; }
exit 0
