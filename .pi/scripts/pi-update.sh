#!/bin/sh
set -e
pi update "$@"
exec "$(dirname "$0")/patch-open-agents.sh"
