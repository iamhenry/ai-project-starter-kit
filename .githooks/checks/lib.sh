#!/usr/bin/env bash
# Shared helpers for the hook checks. Sourced, never executed.

# is_binary <object-spec>
# True when the blob holds a NUL byte in its first 8 KB.
is_binary() {
  local raw text
  raw=$(git cat-file blob "$1" 2>/dev/null | head -c 8000 | wc -c | tr -d ' ')
  text=$(git cat-file blob "$1" 2>/dev/null | head -c 8000 | tr -d '\000' | wc -c | tr -d ' ')
  [ "$raw" != "$text" ]
}

# skipped <path>
# True when the path matches a glob in .githooks/skip.
skipped() {
  local path=$1 pat
  [ -f "$SKIP_FILE" ] || return 1
  while IFS= read -r pat || [ -n "$pat" ]; do
    case $pat in ''|\#*) continue ;; esac
    # shellcheck disable=SC2254
    case $path in $pat) return 0 ;; esac
  done < "$SKIP_FILE"
  return 1
}

# excluded_from_size <path>
# Prose may be long; source code may not. Add another format here if needed.
excluded_from_size() {
  case $1 in
    *.md|*.mdx) return 0 ;;
  esac
  return 1
}

# gitleaks_scan <staged | push> [base head]
# Gitleaks output is captured; only a safe rule and file location are printed.
gitleaks_scan() {
  local mode=$1 base=${2:-} head=${3:-} repo tmp report status log_opts
  if ! command -v gitleaks >/dev/null 2>&1; then
    if [ "${GITLEAKS_MISSING_WARNED:-}" != 1 ]; then
      cat <<'EOF'

  !!! gitleaks is not installed. This hook will use its built-in checks only.
      To add broader secret checks, you can install it with: brew install gitleaks
      Installation is optional and needs your approval. This hook will not install it.

EOF
      GITLEAKS_MISSING_WARNED=1
    fi
    return 0
  fi

  repo=$(git rev-parse --show-toplevel) || {
    printf '  ✗ gitleaks could not find the repository root; blocked.\n'
    return 1
  }
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gitleaks-hook.XXXXXX") || {
    printf '  ✗ gitleaks could not create a temporary report; blocked.\n'
    return 1
  }
  printf '{{range .}}  ✗ {{.File}}:{{.StartLine}}  {{.RuleID}}\n{{end}}' >"$tmp/report.tmpl"

  if [ "$mode" = staged ]; then
    gitleaks git --staged --config "$here/gitleaks.toml" \
      --redact --no-banner --exit-code 42 --report-format template \
      --report-template "$tmp/report.tmpl" --report-path - "$repo" >"$tmp/report" 2>/dev/null
    status=$?
  else
    if [ -n "$base" ] && [ -z "$(printf %s "$base" | tr -d 0)" ]; then
      log_opts="-m $head --not --remotes"
    else
      log_opts="-m $base..$head"
    fi
    gitleaks git --log-opts "$log_opts" --config "$here/gitleaks.toml" \
      --redact --no-banner --exit-code 42 --report-format template \
      --report-template "$tmp/report.tmpl" --report-path - "$repo" >"$tmp/report" 2>/dev/null
    status=$?
  fi

  report=$(cat "$tmp/report")
  rm -rf "$tmp"
  if [ "$status" -eq 0 ]; then
    return 0
  elif [ "$status" -eq 42 ]; then
    [ -n "$report" ] && printf '%s\n' "$report"
    printf '  gitleaks found a secret. Blocked; matched values are hidden.\n'
  else
    printf '  ✗ gitleaks could not complete (exit %s). Blocked as a precaution.\n' "$status"
  fi
  return 1
}

# staged_files
# NUL-separated paths changed in the index.
staged_files() {
  git diff --cached --name-only -z --diff-filter=ACMR
}
