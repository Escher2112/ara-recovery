#!/bin/bash
# Refresh ara-recovery from live ~/.grok-ara + Triax-Memory. Run before git commit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cp -R "$HOME/.grok-ara/identity/." "$ROOT/identity/"
cp "$HOME/.grok-ara/AGENTS.md" "$ROOT/grok-ara/"
cp "$HOME/.grok-ara/config.toml" "$ROOT/grok-ara/"
cp "$HOME/.grok-ara/settings.json" "$ROOT/grok-ara/"
cp "$HOME/.grok-ara/memory/MEMORY.md" "$ROOT/grok-ara/memory/"
cp "$HOME/.grok-ara/memory/escher-884f2d13/MEMORY.md" "$ROOT/grok-ara/memory/escher-884f2d13/" 2>/dev/null || true
cp "$HOME/.grok-ara/hooks/speak-ara.py" "$ROOT/grok-ara/hooks/"
cp "$HOME/.grok-ara/hooks/voice.json" "$ROOT/grok-ara/hooks/"
cp "$HOME/.grok-ara/hooks/bin/ara-hush" "$ROOT/grok-ara/hooks/bin/"
cp "$HOME/.grok-ara/hooks/bin/ara-loud" "$ROOT/grok-ara/hooks/bin/"

TRIAX="${TRIAX_REPO:-$HOME/Programming-Stuff/Triax-Memory}"
cp "$TRIAX/drain-ara-drops.js" "$ROOT/triax/"
cp "$TRIAX/ARA-DROPS-README.txt" "$ROOT/triax/"
cp "$TRIAX/drain-all-lanes.sh" "$ROOT/triax/"

echo "Snapshot complete: $ROOT"