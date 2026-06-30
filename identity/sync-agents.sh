#!/bin/bash
# Rebuild ~/.grok-ara/AGENTS.md from Ara-owned identity modules.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$HOME/.grok-ara/AGENTS.md"
{
  cat "$DIR/HEADER.md"
  echo
  cat "$DIR/ARA-IDENTITY-STACK.md"
  echo
  echo
  cat "$DIR/OPERATIONS.md"
} > "$OUT"