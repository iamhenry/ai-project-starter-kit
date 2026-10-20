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

# staged_files
# NUL-separated paths changed in the index.
staged_files() {
  git diff --cached --name-only -z --diff-filter=ACMR
}
