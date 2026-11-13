#!/bin/sh
# One command for every hivecall suite.
set -e
cd "$(dirname "$0")"
bun test test/
(cd watchdog && python3 -m unittest -q test_watch)
(cd eval && python3 -m unittest -q test_eval)
python3 watchdog/compare/compare.py
