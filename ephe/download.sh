#!/usr/bin/env bash
# Fetches the Swiss Ephemeris data files starcharts currently relies on
# for dates outside Moshier's native range (~3002 BCE - ~3003 CE). See
# README.md in this directory for the naming convention and how to
# extend coverage further back.
set -euo pipefail
cd "$(dirname "$0")"

BASE="https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"
FILES=(
  seplm30.se1 seplm36.se1 seplm42.se1 seplm48.se1 seplm54.se1
  semom30.se1 semom36.se1 semom42.se1 semom48.se1 semom54.se1
)

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "already have $f"
  else
    curl -sS --max-time 60 -o "$f" "$BASE/$f"
    echo "downloaded $f"
  fi
done
