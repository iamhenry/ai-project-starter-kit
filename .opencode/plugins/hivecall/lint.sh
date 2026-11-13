#!/bin/sh
set -eu
cd "$(dirname "$0")"

bunx @biomejs/biome@2.3.12 lint .
pipx run --spec pylint==4.1.3 pylint --rcfile=.pylintrc --recursive=y .
