#!/bin/sh
# One command for every hivecall suite.
set -e
cd "$(dirname "$0")"
bun test test/ 2>&1 | tail -4
(cd watchdog && python3 -m unittest test_watch 2>&1 | tail -2)
(cd eval && python3 -m unittest test_eval 2>&1 | tail -2)
