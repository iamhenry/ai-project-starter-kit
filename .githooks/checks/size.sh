#!/usr/bin/env bash
# Blocks files over the token budget. Tokens are estimated as bytes / 4.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
SKIP_FILE="$here/../skip"
# shellcheck source=lib.sh
. "$here/lib.sh"

LIMIT_TOKENS=${LIMIT_TOKENS:-5000}
LIMIT_BYTES=$((LIMIT_TOKENS * 4))
prefix=$1
found=0

while IFS= read -r -d '' f; do
  skipped "$f" && continue
  excluded_from_size "$f" && continue
  if ! size=$(git cat-file -s "$prefix$f" 2>/dev/null); then
    printf '\n  ✗ %s — could not read the staged content. Blocked as a precaution.\n' "$f"
    found=$((found + 1))
    continue
  fi
  [ "$size" -le "$LIMIT_BYTES" ] && continue
  is_binary "$prefix$f" && continue

  found=$((found + 1))
  cat <<EOF

  ✗ $f — $((size / 4)) tokens (limit $LIMIT_TOKENS)

    How to split:
      1. Keep one concern per file. Leave the original path as a thin re-export so callers don't change.
      2. Move examples, fixtures and long prose beside it (${f%.*}-examples.md) and link them from the original.
      3. Aim for under 2,000 tokens per file; around 500 is comfortable to hold in one pass.
      4. Vendored or generated? Add a glob to .githooks/skip instead of touching this file.
EOF
done

if [ "$found" -gt 0 ]; then
  printf '\n  %s file(s) blocked. Token budget: %s per source file.\n' "$found" "$LIMIT_TOKENS"
  printf '  One-off override: SKIP_HOOKS=1 git commit ...\n\n'
  exit 1
fi
exit 0
