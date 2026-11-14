#!/usr/bin/env bash
set -uo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
tmpbase=${TMPDIR:-/tmp}/guard-tests
rm -rf "$tmpbase"; mkdir -p "$tmpbase"
passed=0; failed=0
alpha=abcdefghijklmnopqrstuvwxyz0123456789
host=$(hostname -s 2>/dev/null || true)
hook_override=SKIP"_HOOKS"

setup() {
  case_dir="$tmpbase/$1"; rm -rf "$case_dir"; mkdir -p "$case_dir"
  git init -q --bare "$case_dir/remote.git"; git init -q "$case_dir/repo"
  cd "$case_dir/repo" || exit 2
  git config user.email 'builder@example.com'; git config user.name Guard
  git config core.hooksPath "$root/.githooks"
  git remote add origin "$case_dir/remote.git"
  printf 'seed baseline\n' >file.txt; git add file.txt
  git -c core.hooksPath=/dev/null commit -qm seed
  git push -q origin HEAD:main >/dev/null 2>&1 || return 1
  before=$(git --git-dir="$case_dir/remote.git" rev-parse refs/heads/main)
}
commit_case() { git add -A && git -c core.hooksPath=/dev/null commit -qm case; }
record() {
  local name=$1 rc=$2 out=$3 mode=$4 rule=$5 secret=${6:-} after changed ok=1
  after=$(git --git-dir="$case_dir/remote.git" rev-parse refs/heads/main 2>/dev/null || true)
  changed=0; [ "$before" != "$after" ] && changed=1
  if [ "$mode" = block ]; then
    [ "$rc" -ne 0 ] && [ "$changed" -eq 0 ] && [[ "$out" == *"$rule"* ]] || ok=0
  else
    [ "$rc" -eq 0 ] && [ "$changed" -eq 1 ] || ok=0
  fi
  if [ -n "$secret" ] && grep -Fq -- "$secret" <<<"$out"; then ok=0; fi
  if [ "$ok" -eq 1 ]; then echo "PASS $name"; passed=$((passed+1)); else echo "FAIL $name rc=$rc changed=$changed expected=$mode rule=$rule output=$out"; failed=$((failed+1)); fi
}
push_case() { local name=$1 mode=$2 rule=${3:-} secret=${4:-} out rc; out=$(git push origin HEAD:main 2>&1); rc=$?; record "$name" "$rc" "$out" "$mode" "$rule" "$secret"; }
case_run() {
  local name=$1 value=$2 rule=$3 mode=$4 path
  setup "$name" || return
  case "$name" in jsonl) path=log.jsonl ;; ndjson) path=log.ndjson ;; session-path) path=sessions/log.txt ;; *) path=file.txt ;; esac
  mkdir -p "$(dirname "$path")"; printf '%s\n' "${value:-clean update}" >"$path"; commit_case
  push_case "$name" "$mode" "$rule" "$value"
}

case_run clean '' '' pass
case_run home "/Users/$USER/private" home-path block
home_line="++ /Users/$USER/$(printf 'guard')"; case_run plus-home "$home_line" home-path block "$home_line"
case_run linux-home "/home/$USER/private" home-path block
thr="thr""_abcdefghij"; proj="proj""_abcdefghij"; ses="ses""_abcdefghijklmnopqrstuvwx"
case_run thread "$thr" bb-id block
case_run project "$proj" bb-id block
case_run session "$ses" bb-id block
plus_path="++ b/$thr"; case_run plus-path "$plus_path" bb-id block "$thr"
mail="person@$(printf 'mail')$(printf '.com')"; case_run email "$mail" email block
case_run jsonl traceprobe trace-file block
case_run ndjson traceprobe trace-file block
case_run session-path traceprobe trace-file block
tsnet="secure.private.ts"".net"; case_run tsnet "$tsnet" private-host block
if [ "${#host}" -ge 4 ] && [ "$host" != localhost ]; then case_run hostname "$host" private-host block; fi
case_run example-email "person@$(printf 'example.com')" '' pass
case_run pkg-email 'pkg@1.2.3' '' pass
case_run remote-user 'git@github.com' '' pass

# A secret in an earlier pushed commit must remain visible to the scanner even
# when a later commit removes it. Values are assembled so test data is harmless.
secret_prefix=AKIA; secret_suffix=ABCDEFGHIJKLMNOP; dummy_secret="$secret_prefix$secret_suffix"
setup add-delete
printf '%s\n' "$dummy_secret" >file.txt; git add file.txt
git -c core.hooksPath=/dev/null commit -qm add-dummy
offending=$(git rev-parse --short HEAD)
printf 'clean update\n' >file.txt; git add file.txt
git -c core.hooksPath=/dev/null commit -qm delete-dummy
out=$(git push origin HEAD:main 2>&1); rc=$?
after=$(git --git-dir="$case_dir/remote.git" rev-parse refs/heads/main)
if [ "$rc" -ne 0 ] && [ "$before" = "$after" ] && [[ "$out" == *"$offending"* ]]; then echo 'PASS add-delete-commit'; passed=$((passed+1)); else echo "FAIL add-delete-commit rc=$rc output=$out"; failed=$((failed+1)); fi

# The zero remote SHA path for a new branch must scan commits not on remotes.
setup new-branch-add-delete
git switch -q -c fresh-branch
printf '%s\n' "$dummy_secret" >file.txt; git add file.txt
git -c core.hooksPath=/dev/null commit -qm add-dummy
offending=$(git rev-parse --short HEAD)
printf 'clean update\n' >file.txt; git add file.txt
git -c core.hooksPath=/dev/null commit -qm delete-dummy
zero=0000000000000000000000000000000000000000
out=$(printf 'refs/heads/fresh-branch %s refs/heads/fresh-branch %s\n' "$(git rev-parse HEAD)" "$zero" | "$root/.githooks/pre-push" 2>&1); rc=$?
if [ "$rc" -ne 0 ] && [[ "$out" == *"$offending"* ]]; then echo 'PASS new-branch-add-delete'; passed=$((passed+1)); else echo "FAIL new-branch-add-delete rc=$rc output=$out"; failed=$((failed+1)); fi

# Three ordinary commits remain pushable.
setup clean-three
for n in one two three; do printf '%s\n' "$n" >>file.txt; git add file.txt; git -c core.hooksPath=/dev/null commit -qm "$n"; done
push_case clean-three pass

# A private path in only the middle commit must identify that commit and leave
# the remote unchanged.
setup private-middle
printf 'first\n' >>file.txt; git add file.txt; git -c core.hooksPath=/dev/null commit -qm first
private_prefix=/Users/; private_user=dummy-user; private_path="$private_prefix$private_user/private"
printf '%s\n' "$private_path" >>file.txt; git add file.txt; git -c core.hooksPath=/dev/null commit -qm middle
offending=$(git rev-parse --short HEAD)
printf 'last\n' >>file.txt; git add file.txt; git -c core.hooksPath=/dev/null commit -qm last
out=$(git push origin HEAD:main 2>&1); rc=$?
after=$(git --git-dir="$case_dir/remote.git" rev-parse refs/heads/main)
if [ "$rc" -ne 0 ] && [ "$before" = "$after" ] && [[ "$out" == *"$offending"* ]]; then echo 'PASS private-middle-commit'; passed=$((passed+1)); else echo "FAIL private-middle-commit rc=$rc output=$out"; failed=$((failed+1)); fi

setup ignored-file
printf 'secret-build-output\n' >ignored.dat; echo ignored.dat >.gitignore; git add .gitignore; git add -f ignored.dat; commit_case
push_case ignored-file block ignored-file
setup ignored-allowed
printf 'secret-build-output\n' >ignored.dat; echo ignored.dat >.gitignore; printf 'ignored.dat ignored-file # generated artifact\n' >.githooks-allow; git add .gitignore .githooks-allow; git add -f ignored.dat; commit_case
push_case ignored-allowed pass ''
setup large-file
dd if=/dev/zero of=large.bin bs=1024 count=250 2>/dev/null; commit_case; push_case large-file block large-file
for allow_line in 'large.bin large-file # reviewed fixture' 'large.bin large-file #' 'large.bin large-file'; do
  name=large-allowed; [[ "$allow_line" == *'# reviewed'* ]] || name=large-no-reason
  setup "$name"; dd if=/dev/zero of=large.bin bs=1024 count=250 2>/dev/null
  printf '%s\n' "$allow_line" >.githooks-allow; commit_case
  out=$(git push origin HEAD:main 2>&1); rc=$?
  if [[ "$name" == *no-reason* ]]; then
    after=$(git --git-dir="$case_dir/remote.git" rev-parse refs/heads/main); changed=0; [ "$before" != "$after" ] && changed=1
    if [ "$rc" -ne 0 ] && [ "$changed" -eq 0 ] && [[ "$out" == *'.githooks-allow:1 ignored: no reason'* ]] && [[ "$out" == *large-file* ]]; then echo 'PASS large-no-reason'; passed=$((passed+1)); else echo "FAIL large-no-reason rc=$rc output=$out"; failed=$((failed+1)); fi
  else record large-allowed "$rc" "$out" pass '' ''; fi
done
setup line-allow
line_mail="person@$(printf mail)$(printf '.com')"; printf '%s\n' "$line_mail" >file.txt; printf 'file.txt email # approved test value\n' >.githooks-allow; git add .githooks-allow file.txt; commit_case; push_case line-allow pass

setup unknown-sha
printf 'clean change\n' >file.txt; commit_case
unknown=ffffffffffffffffffffffffffffffffffffffff
out=$(printf 'refs/heads/main %s refs/heads/main %s\n' "$(git rev-parse HEAD)" "$unknown" | "$root/.githooks/pre-push" 2>&1); rc=$?
if [ "$rc" -ne 0 ] && [[ "$out" == *'could not run'* ]] && [[ "$out" == *blocked* ]]; then echo 'PASS unknown-sha'; passed=$((passed+1)); else echo "FAIL unknown-sha rc=$rc output=$out"; failed=$((failed+1)); fi

setup secret
token="ghp""_$(printf '%036d' 0 | tr 0 a)"; printf '%s\n' "$token" >file.txt; commit_case; push_case secret block github-token "$token"
setup skip-private-detail
private_detail="/Users/$(printf dummy-user)/private"
printf '%s\n' "$private_detail" >file.txt; commit_case
out=$(env "$hook_override=1" git push origin HEAD:main 2>&1); rc=$?
record skip-private-detail "$rc" "$out" block home-path
setup old-history
printf '%s\n' "$token" >file.txt; git add file.txt; git -c core.hooksPath=/dev/null commit -qm old-secret
git -c core.hooksPath=/dev/null push -q origin HEAD:main
before=$(git --git-dir="$case_dir/remote.git" rev-parse refs/heads/main)
printf 'safe later update\n' >file.txt; commit_case; push_case old-history pass

echo "RESULT passed=$passed failed=$failed"
[ "$failed" -eq 0 ]
