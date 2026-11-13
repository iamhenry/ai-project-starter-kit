#!/usr/bin/env bash
set -uo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
tmpbase=$(mktemp -d "${TMPDIR:-/tmp}/check-hook.XXXXXX")
passed=0; failed=0
trap 'rm -rf "$tmpbase"' EXIT
setup() {
  case_dir="$tmpbase/$1"; mkdir -p "$case_dir"
  git init -q "$case_dir/repo" || return 1
  cd "$case_dir/repo" || return 1
  git config user.email builder@example.com; git config user.name Builder
  git config core.hooksPath "$root/.githooks"
  printf 'seed\n' >file.txt; git add file.txt
  git -c core.hooksPath=/dev/null commit -qm seed
  before=$(git rev-parse HEAD)
}
result() {
  local name=$1 ok=$2 detail=${3:-}
  if [ "$ok" -eq 1 ]; then echo "PASS $name"; passed=$((passed+1)); else echo "FAIL $name $detail"; failed=$((failed+1)); fi
}
make_check() { printf '%s\n' "$1" >check; chmod "$2" check; }
commit_update() { printf 'update\n' >file.txt; git add file.txt; git commit -m case 2>&1; }

setup fail
make_check $'#!/bin/sh\necho UNIQUE_CHECK_FAILURE\nexit 1' 755
out=$(commit_update); rc=$?; after=$(git rev-parse HEAD)
if [ "$rc" -ne 0 ] && [ "$before" = "$after" ] && [[ "$out" == *UNIQUE_CHECK_FAILURE* ]]; then result fail 1; else result fail 0 "rc=$rc output=$out"; fi

setup pass
make_check $'#!/bin/sh\nexit 0' 755
out=$(commit_update); rc=$?; after=$(git rev-parse HEAD)
if [ "$rc" -eq 0 ] && [ "$before" != "$after" ]; then result pass 1; else result pass 0 "rc=$rc"; fi

setup isolated-git
cat >check <<'EOF'
#!/usr/bin/env bash
set -e
inner=$(mktemp -d "${TMPDIR:-/tmp}/check-hook-inner.XXXXXX")
trap 'rm -rf "$inner"' EXIT
git init -q "$inner/repo"
cd "$inner/repo"
[[ "$(git rev-parse --absolute-git-dir)" -ef "$inner/repo/.git" ]] || { echo "git did not select the temp repository" >&2; exit 1; }
printf 'inner\n' >inner.txt
git add inner.txt
git -c user.name=Builder -c user.email=builder@example.com -c core.hooksPath=/dev/null commit -qm inner
EOF
chmod +x check
printf 'update\n' >file.txt; git add file.txt
out=$(GIT_DIR="$PWD/.git" GIT_INDEX_FILE="$PWD/.git/index" git commit -m case 2>&1); rc=$?; after=$(git rev-parse HEAD)
if [ "$rc" -eq 0 ] && [ "$before" != "$after" ]; then result isolated-git 1; else result isolated-git 0 "rc=$rc output=$out"; fi

setup none
baseline="$tmpbase/base-hooks"; mkdir -p "$baseline/checks"
git -C "$root" show ad3fb3c:.githooks/pre-commit | sed '/^staged_files |/d' >"$baseline/pre-commit"
for file in lib.sh secrets.sh; do ln -s "$root/.githooks/checks/$file" "$baseline/checks/$file"; done
ln -s "$root/.githooks/gitleaks.toml" "$baseline/gitleaks.toml"
chmod +x "$baseline/pre-commit"
printf 'update\n' >file.txt; git add file.txt
base_out=$("$baseline/pre-commit" 2>&1); base_rc=$?
current_out=$("$root/.githooks/pre-commit" 2>&1); current_rc=$?
git config core.hooksPath "$root/.githooks"
commit_out=$(git commit -m case 2>&1); commit_rc=$?
if [ "$base_rc" -eq "$current_rc" ] && [ "$base_out" = "$current_out" ] && [ "$current_rc" -eq 0 ] && [ "$commit_rc" -eq 0 ]; then result none 1; else result none 0 "base_rc=$base_rc current_rc=$current_rc commit_rc=$commit_rc base_output=$base_out current_output=$current_out"; fi

setup large-file
head -c 21001 /dev/zero | tr '\000' x >large.ts
git add large.ts
out=$(git commit -m case 2>&1); rc=$?; after=$(git rev-parse HEAD)
if [ "$rc" -eq 0 ] && [ "$before" != "$after" ]; then result large-file 1; else result large-file 0 "rc=$rc"; fi

setup dummy-secret
dummy_key="AKIA""0000000000000000"
printf '%s\n' "$dummy_key" >dummy-key.txt; git add dummy-key.txt
out=$(git commit -m case 2>&1); rc=$?; after=$(git rev-parse HEAD)
if [ "$rc" -ne 0 ] && [ "$before" = "$after" ] && [[ "$out" == *aws-access-key* ]] && [[ "$out" != *"$dummy_key"* ]]; then result dummy-secret 1; else result dummy-secret 0 "rc=$rc"; fi

setup non-executable
printf '#!/bin/sh\nexit 1\n' >check; chmod 644 check
out=$(commit_update); rc=$?; if [ "$rc" -eq 0 ] && [ "$before" != "$(git rev-parse HEAD)" ]; then result non-executable 1; else result non-executable 0 "rc=$rc"; fi

setup skip
make_check $'#!/bin/sh\necho SHOULD_NOT_RUN\nexit 1' 755
printf 'update\n' >file.txt; git add file.txt
out=$(SKIP_HOOKS=1 git commit -m case 2>&1); rc=$?; if [ "$rc" -eq 0 ] && [ "$before" != "$(git rev-parse HEAD)" ] && [[ "$out" != *SHOULD_NOT_RUN* ]]; then result skip 1; else result skip 0 "rc=$rc output=$out"; fi

echo "RESULT passed=$passed failed=$failed"
[ "$failed" -eq 0 ]
